# 인스타툰 이미지 생성용 MCP 설치 (Windows)

Claude Code에서 OpenAI GPT Image로 이미지를 만들 수 있게 연결합니다.
Claude 앱과 Claude Code는 이미 쓰고 있다고 가정합니다.

## 순서

1. **Node.js 설치**: https://nodejs.org 에서 LTS 버전 설치 (22 이상 필요)
2. **OpenAI 가입**: https://platform.openai.com (ChatGPT 구독과 별개)
3. **결제 등록**: Billing에서 카드 등록 후 크레딧 충전
4. **조직 인증**: Settings → Organization → General → Verify Organization (신분증 인증, 반영에 시간이 걸릴 수 있음)
5. **API 키 발급**: API keys → Create new secret key → 권한 All → `sk-`로 시작하는 키를 메모장에 복사
6. **압축 풀기**: 이 폴더의 ZIP을 받았다면 반드시 압축을 푼 뒤 진행
7. **Claude 앱 완전 종료**: 창을 닫고, 트레이 아이콘(작업 표시줄 오른쪽 아래)에서도 종료
8. **`install.bat` 더블클릭**: 파란 경고창이 뜨면 "추가 정보 → 실행"
9. **키 붙여넣기 후 엔터**: 별표로 보이거나 아무것도 안 보여도 정상
10. **질문 2개에 엔터**: 권한 허용, 시험 이미지 생성 (시험 이미지는 크레딧이 소량 차감)
11. **`시험 이미지 생성 성공`과 `설치 완료` 확인** 후 아무 키나 눌러 창 닫기
12. **Claude 앱 실행**: 이제 이미지 생성 요청을 하면 됩니다

만든 이미지는 `내 PC\다운로드\openai-images` 폴더에 저장됩니다.

## 설치 창에 나오는 메시지별 해결

| 메시지 | 해결 |
|---|---|
| 조직 인증 필요 | Verify Organization 완료 후 Claude에서 다시 시도 (재설치 불필요) |
| 크레딧이 부족 | Billing에서 충전 후 Claude에서 다시 시도 (재설치 불필요) |
| 이미지 생성 권한이 없습니다 | 키 권한 All로 새로 발급 후 `install.bat` 다시 실행 |
| OpenAI가 키를 거부 | 키를 다시 복사하거나 새로 발급 후 다시 실행 |
| Node.js ... 너무 낮습니다 | nodejs.org에서 LTS 설치 후 다시 실행 |
| OpenAI 접속 실패 / MCP 서버를 받거나 켜지 못했습니다 | 인터넷, 회사 방화벽·VPN 확인 후 다시 실행 |
| 설정 파일 수정 실패 | Claude 완전 종료 후 다시 실행 |
| `setup-gpt-image-mcp.ps1 not found` | ZIP 압축을 풀고 그 안에서 실행 |

`install.bat`은 여러 번 실행해도 안전합니다. 실행할 때마다 기존 설정을 백업하고 다시 등록합니다.

## 설치 후 Claude에서 이미지 도구가 안 보이면

- Claude 앱을 트레이까지 완전히 종료한 뒤 다시 실행
- Node.js를 방금 설치했다면 컴퓨터 재시작
- 그래도 안 되면 `install.bat` 다시 실행

## 주의

- API 키는 `%USERPROFILE%\.claude.json` 과 같은 위치의 백업 파일(`.claude.json.backup-날짜`)에 암호화 없이 저장됩니다. 이 파일들을 남에게 보내지 마세요.
- 이 폴더에는 키가 들어 있지 않으므로 다른 사람에게 줘도 됩니다.
- 이미지 생성은 장당 과금됩니다.
- 이미지는 기본 저장 폴더(`다운로드\openai-images`) 안에만 저장됩니다. 다른 폴더가 필요하면 Claude에게 저장 후 옮겨 달라고 요청하세요.
