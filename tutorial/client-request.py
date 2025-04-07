import os
import requests
from openai import OpenAI, APIError
import json # JSON 파싱을 위해 추가

os.environ['OPENAI_API_KEY'] = 'Your OpenAI API Key'
# --- 설정 ---
# 실제 MCP 서버 URL로 변경하세요.
MCP_SERVER_URL = "localhost:6274" # MCP 서버 URL
# 사용할 OpenAI 모델 (예: "gpt-4", "gpt-3.5-turbo")
OPENAI_MODEL = "s"

# --- MCP 서버 통신 함수 ---

def get_mcp_data(endpoint):
    """지정된 엔드포인트에서 MCP 서버로부터 데이터를 가져옵니다."""
    url = f"{MCP_SERVER_URL}/{endpoint}"
    try:
        response = requests.get(url, timeout=10) # 타임아웃 설정
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"MCP 서버 '{url}' 연결 오류: {e}")
        return None
    except json.JSONDecodeError:
        print(f"MCP 서버 '{url}'에서 잘못된 JSON 응답을 받았습니다.")
        print(f"응답 내용: {response.text}")
        return None

def get_tools():
    """MCP 서버에서 도구 목록을 가져옵니다."""
    print("MCP 서버에서 도구 목록을 가져오는 중...")
    tools = get_mcp_data("tools/list")
    if tools:
        print("사용 가능한 도구:")
        if isinstance(tools, list):
             for i, tool in enumerate(tools):
                 # 도구 형식이 딕셔너리이고 'name' 키가 있다고 가정
                 if isinstance(tool, dict) and 'name' in tool:
                     print(f"- {tool.get('name', '이름 없음')}")
                 else:
                     print(f"- {tool}") # 단순 문자열 리스트일 경우
        else:
             print("- ", tools) # 리스트가 아닌 다른 형식일 경우
        print("-" * 20)
    return tools

def get_prompts():
    """MCP 서버에서 프롬프트 목록을 가져옵니다."""
    print("MCP 서버에서 프롬프트 목록을 가져오는 중...")
    prompts_data = get_mcp_data("prompts")
    if prompts_data:
        print("사용 가능한 프롬프트:")
        if isinstance(prompts_data, list):
            for i, prompt_info in enumerate(prompts_data):
                # 프롬프트 정보가 딕셔너리이고 'name' 키가 있다고 가정
                if isinstance(prompt_info, dict) and 'name' in prompt_info:
                     print(f"{i + 1}. {prompt_info.get('name', '이름 없는 프롬프트')}")
                else:
                    print(f"{i + 1}. 프롬프트 {i+1} (형식 정보 없음)")
        else:
            print("- 프롬프트 데이터를 리스트 형식으로 가져오지 못했습니다.")
        print("-" * 20)
    return prompts_data

# --- OpenAI GPT 호출 함수 ---

def call_openai_gpt(client, prompt_text):
    """주어진 프롬프트로 OpenAI GPT 모델을 호출합니다."""
    print("\nOpenAI GPT 모델 호출 중...")
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )
        # print("API 응답:", completion) # 디버깅용
        if completion.choices:
             return completion.choices[0].message.content.strip()
        else:
             print("API 응답에서 유효한 선택지를 찾을 수 없습니다.")
             return None
    except APIError as e:
        print(f"OpenAI API 오류 발생: {e}")
        return None
    except Exception as e:
        print(f"GPT 호출 중 예기치 않은 오류 발생: {e}")
        return None

# --- 메인 실행 로직 ---

if __name__ == "__main__":
    # 1. OpenAI API 키 확인 및 클라이언트 초기화
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("오류: 환경 변수 'OPENAI_API_KEY'가 설정되지 않았습니다.")
        exit()

    try:
        openai_client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"OpenAI 클라이언트 초기화 실패: {e}")
        exit()

    # 2. MCP 서버에서 도구 및 프롬프트 목록 가져오기
    available_tools = get_tools()


    available_prompts = get_prompts()

    if not available_prompts or not isinstance(available_prompts, list):
        print("MCP 서버에서 유효한 프롬프트 목록을 가져오지 못했습니다. 프로그램을 종료합니다.")
        exit()

    # 3. 사용자로부터 프롬프트 선택 받기
    while True:
        try:
            choice = input(f"사용할 프롬프트 번호를 입력하세요 (1-{len(available_prompts)}): ")
            prompt_index = int(choice) - 1
            if 0 <= prompt_index < len(available_prompts):
                selected_prompt_info = available_prompts[prompt_index]
                 # 선택된 프롬프트가 딕셔너리이고 'template' 키를 가지고 있는지 확인
                if isinstance(selected_prompt_info, dict) and 'template' in selected_prompt_info:
                    selected_prompt_template = selected_prompt_info['template']
                    prompt_name = selected_prompt_info.get('name', f'프롬프트 {prompt_index + 1}')
                    print(f"선택된 프롬프트: '{prompt_name}'")
                    print(f"템플릿: {selected_prompt_template}")
                    break
                else:
                    print("선택한 프롬프트에 'template' 정보가 없습니다. 다른 프롬프트를 선택해주세요.")
            else:
                print("잘못된 번호입니다. 다시 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")
        except Exception as e:
            print(f"프롬프트 선택 중 오류 발생: {e}") # 추가 오류 처리

    # 4. 프롬프트 템플릿에 따른 사용자 입력 받기 (예시: 템플릿에 {user_input}이 있다고 가정)
    # 실제 템플릿 구조에 따라 입력 받는 방식을 수정해야 합니다.
    final_prompt = selected_prompt_template
    if "{user_input}" in selected_prompt_template:
        user_input_value = input("프롬프트에 전달할 내용을 입력하세요: ")
        final_prompt = selected_prompt_template.replace("{user_input}", user_input_value)
    elif "{text}" in selected_prompt_template: # 다른 플레이스홀더 예시
        user_input_value = input("텍스트를 입력하세요: ")
        final_prompt = selected_prompt_template.replace("{text}", user_input_value)
    else:
         print("프롬프트 템플릿에 플레이스홀더({user_input} 등)가 없습니다. 템플릿 그대로 사용합니다.")
        # 필요하다면 여기서 사용자 입력을 받는 로직을 추가할 수 있습니다.


    print(f"\n최종 생성된 프롬프트:\n{final_prompt}")
    print("-" * 20)


    # 5. OpenAI GPT 모델 호출 및 결과 출력
    gpt_result = call_openai_gpt(openai_client, final_prompt)

    if gpt_result:
        print("\n--- GPT 응답 결과 ---")
        print(gpt_result)
        print("--- 결과 끝 ---")
    else:
        print("GPT로부터 결과를 얻는 데 실패했습니다.")