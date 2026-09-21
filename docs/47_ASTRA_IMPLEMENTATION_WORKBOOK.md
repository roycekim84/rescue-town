# Astra 구현 작업서 — Rescue Town 시골마을 v1.0

작성2026-09-21. 상태: **실행 가능한 작업 순서 확정 / 게임 구현 미착수**.
현재 작업은 문서 인계다. 아래 산출물 경로와 명령 중 Unity 관련 항목은 앞으로 만들 대상이지 이미 존재하는 프로그램이 아니다.

## 0. 목표와 읽기 순서
출시 범위는 고양이50종/최대50마리, 건물13종, 한 시골마을, 광고 포함 완결형이다. 프로토타입을 공개하고 나머지를 업데이트로 미루지 않는다.
`AGENTS.md` → [49 최신 사양 우선순위](49_SPEC_AUTHORITY_AND_HANDOFF.md) → [45 기술선정](45_TECH_STACK_DECISIONS.md) → [46 구현기본값](46_RUNTIME_AND_ASSET_BASELINE.md) → 이 작업서 → [48 인수기준](48_RELEASE_ACCEPTANCE.md) 순으로 읽는다.
작업현황은 `data/implementation_plan.json`과 [50 상태판](50_IMPLEMENTATION_STATUS.md)에 기록한다. 값이 없다고 컨셉을 새로 쓰지 않는다.

## 1. 작업 운영
각 M단계를 한 번에 거대한 커밋으로 만들지 말고 구현→검사→증거→커밋으로 나눈다. 가능하면 기능 브랜치/PR을 사용하되 저장소 보호규칙을 먼저 확인한다. main 강제 push, 사용자 변경 덮어쓰기, 과거 데이터 삭제 금지.
한 단계가 실패하면 원인을 고치고 같은 검사를 재실행한다. 외부 계정·실기기·아트 승인에 막히면 해당 증거를 BLOCKED로 남기고 독립된 코드/테스트를 진행할 수 있다. 전체 단계를 PASSED로 올리는 것은 금지한다.
새 기술/플러그인 탐색은 M0에서 선택한 조합이 실제로 막힌 경우에만 제한적으로 한다. 화면 구현 대신 문서만 계속 추가하는 것을 진행으로 보고하지 않는다.

## M0 — 환경과 재현 가능한 프로젝트
입력: AGENTS,45,46,49와 현행 data/. 목표: 같은 clone에서 프로젝트를 재생성·빌드할 수 있음.
작업:
- 실행 컴퓨터의 Unity/Xcode/Android 도구/라이선스/디스크·기기 접근을 확인한다. 접근하지 않은 컴퓨터의 사양을 검증했다고 쓰지 않는다.
- 현재 공식6000.3 정식패치, URP2D, uGUI/TMP, Input System, 2D Animation, JSON, Test Framework 버전을 고정한다.
- GMA11.5.0과 SQLite wrapper1.3.2 후보의 기본 import/compile을 확인한다. 패치교체는 이유와 확인한 release 정보를 남긴다.
- game/RescueTown 생성, namespace/asmdef/Editor bootstrap, scene/prefab 재생성, 콘텐츠 허용목록 및 검증 entry point를 만든다.
- Force Text/Visible Meta, 프로젝트별 작업 잠금, build profiles, 결과 경로를 준비한다. .meta는 추적하고 Library/Temp/Builds/서명파일은 제외한다.
- 아래 Python 기존검사들을 실제 저장소 입력으로 실행한다. 역사적 PASS 개수를 그대로 보고하지 않는다. 차이를 새 결과로 남긴다.
산출물: Unity 프로젝트, lock 파일, `reports/implementation/toolchain.json`, 환경 차단표, 빌드/검사 스크립트.
완료: 에디터 컴파일 성공 + 데이터 검증 성공 + EmptyScene 빌드 + 재생성2회 후 중복/파괴적 diff 없음. Android/iOS 네이티브 smoke도 가능한 즉시 하고, 못 한 것은 M2/M4의 차단항목으로 이관한다. 라이선스 활성화를 우회하지 않는다.

## M1 — 도메인·데이터·저장 핵심
입력: 현행 게임 JSON,41~43,46. Unity 의존 없는 C# 테스트를 우선 작성한다.
- 모든 CatDefinition50/BuildingDefinition13을 읽고 alias·실제 조건식·온보딩 미러를 검증한다.
- 예약→현장→돌봄→정착, 건설결제/완료, 무료재배치, 직원슬롯, 능력·숙련, 발전도, 초기지원, 축제 자격을 구현한다.
- 경제/오프라인은 단일 명령처리와 Clock으로 계산한다. 렌더링 callback은 골드를 만들지 않는다.
- SQLite 저장 어댑터에 상태+지급키+정산cursor를 원자적으로 적용한다. 초기 FakeStore는 테스트용이며 실제SQLite 통과 전 저장완료로 보고하지 않는다.
- DB 어댑터 failure injection, checkpoint, replay, schema오류, 정산분할, 광고계약 FakeAd 테스트를 만든다.
산출물: Domain/Application/Storage 코드, EditMode 테스트, 원본JSON fixture, 저장schema/migration fixture.
완료: 수치계산·정원·지원금·수집·오프라인 불변식 테스트 통과. 시뮬레이션과 C# 결과의 오차원인을 설명한다. 과거 Python 저장검사 소스가 Git에 없으면 계약에서 C# 검사를 재작성하고 실행한다. 없는 파일을 있는 것으로 인용하지 않는다.

## M2 — 보이는 관통 시험 + 실제 첫8마리
- 먼저 별도 DevelopmentFixture에서 CAT_001의 구조→돌봄→정착→배치→일하는 모습→수입→저장/복귀→공식 테스트광고를 연결한다.
- 이 한 마리 fixture는 시작진행 조건을 검증하는 정상세이브가 아니다. Release에 포함하지 않고 센터주민조건을 몰래 완화하지 않는다.
- 정상 NewGame에서는 onboarding대로 첫8마리/센터4/주택·공원/농장 또는 어시장 경로를 구현한다.
- 망고·구름·탄이3마리의 동일정체성 아트 표본을 준비한다. 실제 생성수단이 없으면 placeholder를 표기하고 에셋 작업을 차단한다. 품질표본 승인 전에50마리 양산하지 않는다.
- 마을pan/zoom, 실제 ResidentView, 프로필/따라가기, 건물cutaway, 직원선택, 지원금알림과 실제수입을 연결한다.
- Android/iOS에서 실제SQLite 쓰기/재실행과 테스트광고 callback을 확인한다. 미디에이션 없는 기본 AdMob 경로부터 한다.
완료: 정상 두 초기시설 경로 플레이 영상, 동일 고양이 구조/프로필/근무 비교, 저장재실행 결과, 테스트광고/실기기 로그. 20~30분은 사용자 플레이 목표이지 가상시계 PASS로 대체하지 않는다.

## M3 — 시골마을 전체 기능과50마리
- 36×36 출발 레이아웃에25개 필지(주택13+나머지12), 입구/경로/작업/휴식slot 데이터를 작성한다. 좌표·동선 자동 검증.
-13종의 각 레벨·직원슬롯·외형단계·행동·꾸미기slot 구현.13종 모두 추상복제처럼 같은 UI/행동만 갖게 하지 않는다.
- 50개 실제 발견조건, 선택/무작위 미보유대상, 타이머, 돌봄, 동일Resident 생성, #050 최종환영 구현.
- 생활 AI/관계/15종micro-event, 가구24+설비8 제작·해금, 거주배정,50마리도감·검색·정렬·직업숙련 화면 완성.
- 최대30명의 직원과 미배치/외출 주민의 표현, 중복뷰 방지, cutaway 입출입·작업점 충돌을 검사한다.
- 전체 시설·조건을 거쳐 센터10/50마리/발전도1600/광장5/주요시설을 만족하고 축제로 이어지게 한다. 모든 건물MAX를 요구하지 않는다.
완료: time-accelerated developer run과 정상시간 부분 플레이를 각각 남긴다. 가속 결과를 실제 완주일수라 부르지 않는다. 생성 예정이 아닌 실제 interior/appearance/layout 데이터가 존재해야 한다.

## M4 — 실서비스 저장·광고·분석
- SQLite backup2개, 손상검출/복구확인, 업데이트migration, 광고pause와 실제absence 구별을 구현한다.
- UMP/ATT 경계, 초기영업+20분 조건, 복귀추가·단축·부스트, earned/closed 순서, 중복/늦은콜백을 실제어댑터로 확인한다.
- 최소 SSV Worker/D1 서버의 등록·Google서명·중복transaction·조회·보관/삭제·rate limit 테스트를 구현한다. 공개배포/외부계정 설정은 승인 후 수행한다.
- server receipt는 보상증거이며 클라우드 세이브나 전체경제 진위판별기로 확장하지 않는다. 증거 없으면 임의지급하지 않는다.
- 단축대상이 시청 중 먼저 끝난 경우43번의 사전고지 대체안과 기존보상 중복0을 시험하고 경제영향을 기록한다.
- Firebase 분석/오류 기록은 동의/수집설정 후 허용된 ID만 사용. 제3자SDK 수집정보·소유자 설정을 데이터안전 문서에 반영한다.
완료: 48의SAVE/ADS 체크, 실제OS강제종료·오프라인·디스크부족·SSV지연 로그. 가짜광고 버튼이 실제 광고 연동을 대체하지 못한다. 서버·서명권한이 없으면 해당출시조건은 BLOCKED다.

## M5 — 최종 아트·UI·사운드
M2 표본승인 후 범위 안에서 제작한다. 새 이미지를 만들 권한/수단이 없는 에이전트는 생산한 것으로 보고하지 않는다.
- 캐릭터50의 모든 화면/방향/포즈 일관성, 직업overlay,13건물 마일스톤,32꾸미기 데이터와 아트,15생활패턴, 구조 장소를 완성한다.
- 시골 스타일·네 발·큰 paw버튼/고양이동선 유지.51번째 장식주민/수인/미구현 가짜작업을 넣지 않는다.
- 한국어/영어·긴 이름·오드아이/비대칭 무늬·세로/태블릿·안전영역·색각·모션 설정과 사운드 확인.
산출물: asset manifest(원본·가공법·권리·버전·ID),50마리 썸네일/정체성 테스트, 실제 게임 캡처.
완료: placeholder/TODO/깨진리소스0. 새 스타일 승인은 표본1회 중심으로 모으고 매번 컨셉을 재논의하지 않는다.

## M6 — 통합QA·밸런스·회귀
-48 전 항목을 실제 대상빌드에서 시험한다. 기존 Python과 C# 런타임 숫자차이를 비교한다.
- 주택추가비/장식지출/실제발견/광고실패/SSV대체보상을 넣어 무광고·보상형 접속시나리오를 재계산한다.
- 후반 새고양이 최대6.5일 공백은 아직 해결되지 않은 항목이다. 예전240만G실험을 자동 기본값으로 바꾸지 않는다. 실제 세션의 다른 보상과 이탈을 측정한 수정표를 제시하고 수치변경·재검증을 함께 기록한다.
- 대표실기기에서50마리/25건물/실내외·장시간·광고복귀를 측정한다. 30fps/메모리 경고선의 변경도 사유를 기록한다.
- 완주→계속플레이→업데이트→복구를 시험한다. 죽은버튼/진행불가/원장불일치/비밀노출은출시차단.
완료: 재현된P0/P1결함0, 알려진이슈/사용자승인, 실제빌드·증거목록. 편의문구 하나 바꿨다고 기존 실기기 QA가 유효한지 release 후보해시로 확인한다.

## M7 — 릴리스 후보와 소유자 제출
- 고정 release 후보commit/tag, Android AAB/iOS archive, 정확한 패키지/번들ID·아이콘·스크린샷·설명·연령/개인정보·SDK명세·app-ads.txt·지원연락처 준비.
- 테스트/production 광고ID 혼입, debugger/devfixture, 서명비밀 포함, 제출시점 target/SDK요구 위반을 빌드검사로 막는다.
- 실제광고요청 가능 상태와 콘솔의 앱/단위등록을 확인하되 실광고 반복시청·클릭으로 수익을 만들지 않는다.
- 스토어 업로드·공개버튼·결제/서버비용은 소유자 승인 후. 미승인 상태는 ready_for_owner_submission이지 published가 아니다.
완료: 출시후 오류/광고/진행지표 모니터링 경로와 롤백/긴급수정 절차까지 인계. 업데이트 기획은 실제반응 후 한다.

## 2. 구현할 CLI 계약
다음 이름의 entry point와 도구를 M0가 만든다. 현재 이 문서를 쓰는 단계에는 존재한다고 가정하지 않는다.

```sh
# 기존 저장소 검사: 실제출력과 스킵을 기록
python3 -S tools/validate_balance.py
python3 -S tools/test_onboarding_contract.py
python3 -S tools/validate_discovery.py
python3 -S tools/test_discovery_contract.py
python3 -S tools/simulate_integrated_progression.py --include-events
python3 -S tools/test_integrated_progression.py

# M0가 구현할 Unity 진입점. UNITY_EDITOR는 설치검증 후 절대경로 지정
"$UNITY_EDITOR" -batchmode -quit -projectPath game/RescueTown -executeMethod RescueTown.Editor.ProjectBootstrap.ValidateAndGenerate -logFile artifacts/bootstrap.log
"$UNITY_EDITOR" -batchmode -projectPath game/RescueTown -runTests -testPlatform EditMode -testResults artifacts/editmode.xml -logFile artifacts/editmode.log
"$UNITY_EDITOR" -batchmode -projectPath game/RescueTown -runTests -testPlatform PlayMode -testResults artifacts/playmode.xml -logFile artifacts/playmode.log
```

artifacts 디렉터리는 명령 실행 전에 생성한다. 테스트실행에 -quit를 함께 붙이지 않는다. 렌더검사에 -nographics를 붙여 화면검사를 건너뛰지 않는다. 커맨드 성공은 exit code뿐 아니라 XML의 실행/실패/스킵 수와 컴파일로그로 판정한다. 실제기기광고시험은 CLI 테스트를 별도로 보완한다. 공식 CLI 근거는49의S03이다.

## 3. 단계 종료 보고 양식
```text
단계/상태:
소스 commit / 빌드 hash:
이번에 실제 구현한 기능:
실행 명령 / 환경 / 종료코드:
검사 성공·실패·스킵:
실제 화면·기기 로그 위치:
사용자가 해야 하는 인증·설정:
미해결 문제와 다음 첫 작업:
```

첫 구현 요청에서는 M0를 시작하고 통과하면 M1로 이어간다. 실행권한/시간창이 끝날 때 이 양식과 다음 작업을 남겨 이어받는다. 완성된 v1.0이 최종 목표지만 한 번의 응답으로 모든 실기기·스토어 외부절차가 자동 완결된다고 약속하지 않는다.
