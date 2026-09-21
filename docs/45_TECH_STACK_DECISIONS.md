# 기술 선택 ADR-001 — 구현 기준선

작성 2026-09-21. 입력 기준 Git: `30da9a7d7f593ae34641b5d91ec5080fe9587618`.
상태: **기술 방향 선정 / 로컬 도구체인·패키지 조합 미검증**. 설치나 게임 구현을 완료했다는 문서가 아니다.
근거 URL은 [49번 문서](49_SPEC_AUTHORITY_AND_HANDOFF.md)의 S01~S15에 기록한다.

## 1. 선정
| 영역 | 선정 기준 |
|---|---|
| 엔진 | Unity 6.3 LTS, 6000.3 계열의 정식 패치 |
| 화면 | 2D URP 2D Renderer, 직교 카메라, 쿼터뷰 스프라이트 |
| UI | uGUI + TextMeshPro, 세로 기준, Safe Area 반영 |
| 도메인 | 순수 C#, 명시적 command 처리, 주입 가능한 시계/난수/저장/광고 |
| 데이터 | 저장소 JSON을 정규화·검증 후 빌드에 포함; Unity용 Newtonsoft JSON 패키지 |
| 저장 | 로컬 SQLite 트랜잭션 + 검증된 백업2개, 단일 쓰기 큐 |
| SQLite 어댑터 | com.gilzoide.sqlite-net, 공개 README의 1.3.2 태그를 첫 호환성 검사 후보로 선택 |
| 광고 | Google Mobile Ads Unity Plugin 11.5.0 + UMP, AdMob 보상형 |
| 영수증 복구 | 최소 Cloudflare Worker(TypeScript) + D1 SSV 영수증 서비스 |
| 분석 | Firebase Analytics/Crashlytics를 어댑터로 격리, 동의·설정 전에는 no-op |
| 모바일 | Android ARM64 IL2CPP / iOS ARM64 IL2CPP. Mac Editor는 개발 도구이며 별도 PC 출시는 아님 |

Unity/패키지가 특정 조합에서 안정적이라는 벤치마크를 수행한 것은 아니다. 패키지 업데이트·교체는 M0 결과와 변경기록을 근거로 한다.

## 2. 왜 Unity인가
Godot도 명령줄·자동화를 지원한다[S11]. 파일 편집만 보면 Godot/GDScript도 유효한 선택이다. Godot 전체가 모바일에 부적합하다는 결론은 아니다. 다만 C# 모바일 지원의 실험적 표기는 해당 언어 경로의 추가 검증사항이다[S12].
이번 선정 이유는 이미 정한 C#형 데이터/상태 설계, Google의 공식 Unity 광고 인터페이스[S02], 모바일 빌드와 2D 애니메이션을 한 도구체인에서 검증하려는 선택이다. 'Astra가 Unity에서 더 똑똑하다'는 검증되지 않은 주장은 근거로 사용하지 않는다.
Unity 공식 페이지는 6.3 LTS를 2027년12월까지 지원한다고 안내한다[S01]. 이 프로젝트에서는 새 기능보다 버전 고정을 우선한다. Unity MCP나 별도 유료 AI 구독은 필수 의존성으로 두지 않는다. 파일/Editor 스크립트/CLI로 기본 작업 경로를 확보한다[S03].

## 3. 버전 잠금: M0에서 실제 값 확정
엔진 패치 번호를 추측해서 ProjectVersion.txt에 쓰지 않는다. M0는 사용 가능한 6000.3 정식 패치 중 현재 플랫폼·패키지 검사를 통과한 버전을 택해 전체 버전과 changeset을 기록한다.
아래 값을 `game/RescueTown/ProjectSettings/ProjectVersion.txt`, Packages/manifest.json, packages-lock.json 및 `reports/implementation/toolchain.json`에 남긴다.
- 에디터 전체버전/CPU 아키텍처, URP/2D Animation/Input System/TMP/JSON/Test Framework 실제버전.
- 광고 플러그인 및 Android/iOS 네이티브 의존성, EDM4U, UMP 버전.
- SQLite wrapper 태그와 불변 commit SHA, 네이티브 바이너리 해시·라이선스·빌드 정보.
- Xcode/SDK, Android SDK/NDK/JDK/Gradle 실제 조합. 의존성에 latest/floating branch를 쓰지 않는다.
Google 공식 최신 release 조회에서 11.5.0을 확인했다[S02a]. OpenUPM의 공식 가이드 경로를 사용하고 unitypackage와 중복 설치하지 않는다. Android Next-Gen 선택 스위치를 무심코 켜지 말고 먼저 기본 경로로 고정한다.
SQLite wrapper는 커뮤니티 패키지다[S06]. 지원 플랫폼 표기는 출처의 선언이지 우리 IL2CPP/16KB 통과 증거가 아니다. 기존 DLL을 임의 삭제해 경고를 숨기지 말고 필요하면 원본 소스·라이선스가 있는 재빌드를 검증한다.

## 4. 플랫폼 기준과 출시 시 재확인
개발 호환 목표는 Android 8(API26)+ / iOS15+로 시작한다. 이는 우리 제품 범위이며 SDK 또는 플랫폼 정책의 최소값을 그대로 주장하는 것이 아니다.
2026-09-21 확인 기준 Google Play 신규 앱의 target은 API36 이상이다[S08]. 최소 지원 OS와 target을 구분한다. 빌드 시점과 제출 직전에 공식 정책을 다시 확인하여 더 높은 요구가 있으면 반영한다.
iOS는 현재 제출에 필요한 SDK와 호스트 macOS에서 실행 가능한 정식 Xcode를 함께 확인한다[S09]. 광고 quick-start의 최소 Xcode와 App Store 제출 요구를 같은 것으로 취급하지 않는다.
Android 네이티브 라이브러리는 에디터·광고·SQLite를 포함해16KB 페이지 환경 및 ELF/패키지 정렬을 시험한다[S10]. iOS는 실기기 서명 빌드를 반드시 확인한다. 시뮬레이터 성공은 실기기 증거가 아니다.

## 5. SQLite 구체안
`Application.persistentDataPath` 아래 저장소를 사용한다. 단순 PlayerPrefs/JSON 덮어쓰기를 핵심 저장으로 쓰지 않는다.
도메인 상태 snapshot과 지급원장은 **같은 DB 트랜잭션**으로 저장한다. 시작안은 단일 쓰기 큐, journal_mode=DELETE, synchronous=FULL, foreign_keys=ON이다. 실제 PRAGMA 반환값을 기록한다. 백그라운드 DB 처리는 Unity 객체를 건드리지 않는다.
최소 테이블은 saves(saveId, schemaVersion, revision, payload, checksum), commands(commandId, payloadHash, revision), grants(grantId), receipts(receiptId, payload), migrations다. 지급키를 지우며 공간을 줄이지 않는다. snapshot에 있는 상태와 별도 원장이 불일치하지 않도록 커밋 검증한다.
가장 최근 정상 백업2개는 SQLite의 일관된 backup/serialize 절차를 이용한다[S07]. 열린 DB 파일만 복사하지 않는다. 정산 전/업데이트 전 검증된 백업을 만들고, 백업 시점·revision을 사용자에게 보여준다. 실제 손상 복구, 저장공간 부족, 강제종료는 M4에서 시험한다.
클라우드 저장/재설치 복구/기기간 동기화는 v1에 넣지 않는다. 로컬만으로 과거 파일 복원 이후 전역 중복 지급까지 막을 수 있다고 주장하지 않는다. 서버 영수증은 클라우드 마을 저장이 아니다.

## 6. 광고 및 서버
실제 광고 공급자는 AdMob이다. v1 기본 광고는 자발적 보상형3종(복귀추가/시간단축/영업부스트). 배너·앱실행광고·강제 전면광고·IAP는 출시 기본값에서 제외한다. 이는 '광고 없는 출시'가 아니다.
Google 공식 API에 맞춰 UMP 상태 갱신/요청가능 여부/필요한 개인정보 옵션을 처리한다[S04]. iOS 추적 관련 판단은 별도로 처리하고 UMP 응답으로 ATT 권한을 가정하지 않는다[S13]. 승인되지 않은 사용자 추적이나 아동용 설정을 추측해 켜지 않는다.
앱의 rewarded callback은 정규화된 명령으로 단일 처리기에 전달한다. 보상 이벤트/닫힘/광고 수익 이벤트는 서로 다르다[S05]. SDK 콜백 스레드는 고정 가정하지 않고 Unity 접근을 메인 스레드로 전달한다[S02].
SSV 서비스는 v1 출시 검증 대상이다. 등록한 불투명 attempt token, Google 서명, ad unit, transaction_id를 검증하고 지연 영수증을 조회한다[S14]. DB unique 제약으로 중복 영수증을 막는다. 클라이언트의 gold 주장이 진실임을 증명하는 서버는 아니며 전체 경제를 서버 권위형으로 확장하지 않는다.
서버 발급 익명 설치 인증과 저장 계보를 분리하고 비밀은 서버/보안 저장소에만 둔다. 개인정보 최소화, 보관기간·삭제 절차는 배포 전 문서화한다. 런타임 상태를 통째로 보내지 않는다.
서버 장애나 미등록 광고ID에서는 새 보상형 요청을 안전하게 보류하되 오프라인 게임과 기본보상은 정상 작동한다. 보상 증거가 아직 없으면 unresolved를 보존한다. 실제 서버 배포·계정 연결·비용 발생은 Royce 승인 후 한다. 서비스 미배포를 완료로 처리하지 않는다.

## 7. 분석과 외부 권한
Firebase 공식 Unity SDK를 사용한다[S15]. 실제 전송 전 수집 범위·동의·콘솔 설정을 검증한다. tutorial_step, first_business_started, center_upgraded, cat_settled, reward_result, save_error 등을 고정ID로 기록하며 사용자 지정 이름/자유입력을 보내지 않는다.
외부 설정이 없어도 게임 코어와 로컬 테스트는 실행 가능하다. 출시판에서 분석 미설정은 명시적 검토 항목이며 데이터를 실제 수집했다고 주장하지 않는다.
Unity 라이선스·Apple/Google 계정·AdMob·Firebase·Cloudflare 로그인, 서명, 공개배포·제출은 소유자 권한 작업이다. 코드 구현과 계정작업을 구분해 최소한의 요청만 남긴다.
