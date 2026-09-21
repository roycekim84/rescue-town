# 최신 사양 우선순위·결정 기록·인계

작성2026-09-21. 인계 직전 기준 commit `30da9a7d7f593ae34641b5d91ec5080fe9587618`.
이번 인계는 **기술·구현 기본값과작업서**를 추가한다. 경제·고양이능력·정원·발견조건·타이머의 기본값은 변경하지 않는다. 실제엔진/아트/광고/서버를 구현한 것이 아니다.

## 1. 충돌 해결 순서
1. 사용자가 확정한 컨셉: 시골마을1,고양이50,희귀도/캐릭터레벨없음,직원3,실제동일주민,광고포함완결출시.
2. 아래 담당원본 JSON과 그 계약문서. 같은 데이터영역에 원본을 두개 만들지 않는다.
3.45~48의 기술선정·미정사양기본값·작업순서·인수조건. 여기서 명시적으로 해결한 후보만 이전예시를 대체한다.
4. 초기문서의연출/콘셉트 예시. 수치와기능후보를새사양처럼복사하지 않는다.
보고서(reports/)는 관측기록이지 런타임설정이 아니다. 파일숫자가높다는이유만으로수치를덮지 않는다. 충돌이해소되지않으면원인과두출처를기록하고임의혼합하지 않는다.

## 2. 영역별 원본
| 영역 | 원본 | 상세 참고 |
|---|---|---|
|50고양이ID/능력/성격|data/cats.json|docs/21~26캐릭터시트 |
|건물13종/5·10레벨/직원|data/buildings.json|16,29 |
|센터조건/정원/축제|data/progression.json|31 |
|발전도|data/development_score.json|31,34 |
|돈/성장/광고수치|data/economy_balance.json|33 |
|초기지원/첫8마리|data/onboarding.json|36 |
|실제발견조건|data/discovery_rules.json|37,38 |
|정상42마리타이머|data/rescue_timing.json|39 |
|저장/정산/보상계약|data/persistence_contract.json|41,42,43 |
|기술방향/의존성후보|45_TECH_STACK_DECISIONS.md|implementation_plan.json |
|지도/주택/아트생산기본값|46_RUNTIME_AND_ASSET_BASELINE.md|M3의검증된실제콘텐츠데이터로구체화 |
|작업과실행상태|47_ASTRA_IMPLEMENTATION_WORKBOOK.md, data/implementation_plan.json|50_IMPLEMENTATION_STATUS.md |

## 3. 이전 초안 중 그대로 사용하면 안 되는 것
- docs/08의14건물/주민회관/여관후보 → 현재13종,여관대신빵집,주민회관없음.
- 주택이구조상한을결정한다는예시 → 센터가정원결정,주택은거주지.13필지/52침상은이번구현기본값.
- 도감50/보유30 → 도감50/최대보유50.동시뷰수와별개.
- 일반Lv10직원해금과센터해금혼동 → 일반1·3·6,센터2·3·5;모두최대3.
- 과거발전도50/3000/3500 → 현행progression.센터3진입0,센터10진입1400,축제1600.
- 최초5500G+추가4500G → 최초1000G+600/2900/1000G,총5500G.
- 밤/비/친구수/화면NPC가필수인발견예시 →37번조건식.분위기는연출이며필수수집조건아님.
- primaryCondition 문자열 → 실행금지,discovery_rules로조인.
- Secret/SSR/희귀고양이우월/성격별숨은상한 → 없음.개성의기본능력+업무숙련.
- 복귀때현재수익×전체시간 →8h창과중간변화적분.광고pause는새absence가아님.
- 예전저장문서의엔진/라이브러리미선정 →45의Unity/SQLite선정으로대체.구현미완료표기는유효.
- 한마리fixture → 내부기술검사.기존센터주민gate를풀거나1마리만출시하지않음.

## 4. 이번 결정 / 기본값 / 소유자 확인
**선정:** Unity6.3 LTS, uGUI/TMP, JSON도메인, SQLite, 공식GMA/UMP, v1보상형광고중심, 최소SSV Worker/D1, 플랫폼실기기검사.
**작업기본값:**36×36격자,주택13필지/최대4,장식24+기능설비8,생활15패턴,Android8+/iOS15+,한국어/영어.변경은콘셉트를지키고QA·변경기록으로한다.
**실행시확정:**정확한에디터패치·Unity패키지버전·의존네이티브라이브러리·기기성능예산.선정과호환검증을구분한다.
**소유자확인:**최종앱명/번들·패키지ID,연령·광고정책의실제대상,계정·광고ID·서버배포·서명,시각표본승인,스토어공개.
엔진전환/유료도입/콘셉트변경은소유자승인사항이다.확인되지않은계정상태를추측해SDK설정으로사용하지않는다.

## 5. 알려진 미완료와 개발 과제
| 항목 | 처리 |
|---|---|
|후반신규고양이공백최대약6.5일(기존모형)|BAL-02로유지,M6재검증.320만G기본을몰래240만으로바꾸지않음 |
|cats정규화파일의얼굴/눈/꼬리등부족|M2표본→M3/M5전체appearance manifest.단순2필드로50마리아트완료선언금지 |
|주택/장식비용을옛모형에서제외|M6에신규필지/카탈로그와통합해비교 |
|SQLite/SDK/SSV 실기기미검증|M2/M4/M6필수검사 |
|Python저장51개참고코드Git미포함|보고서는역사적증거만.41~43에서C#테스트재작성;파일없으면명시 |
|원본·투영입력의차이|기본검사는현행data사용.스냅샷재현을원본실행처럼보고하지않음 |
|아트/스토어실무|모델의도구·권한을먼저확인하고없으면차단.이미지프롬프트만으로실제리소스가생겼다고간주하지않음 |

## 6. 공식·원저자 근거 (2026-09-21 확인)
제출 요구와 SDK 문서는 바뀔 수 있다. M0와제출직전에재확인한다. 아래는기술판단근거이며우리프로젝트에서호환테스트했다는의미가아니다.

- S01 Unity6 릴리스지원: https://unity.com/releases/unity-6/support
- S02 GoogleMobileAdsUnity 설정/패키지/메인스레드: https://developers.google.com/admob/unity/quick-start
- S02a 공식GMA11.5.0 release: https://github.com/googleads/googleads-mobile-unity/releases/tag/v11.5.0
- S03 Unity6.3 CLI: https://docs.unity3d.com/6000.3/Documentation/Manual/EditorCommandLineArguments.html
- S04 UMP: https://developers.google.com/admob/unity/privacy
- S05 Rewarded: https://developers.google.com/admob/unity/rewarded
- S06 SQLite wrapper 원저자 README: https://github.com/gilzoide/unity-sqlite-net
- S07 SQLite 원자적커밋/백업: https://www.sqlite.org/atomiccommit.html ; https://www.sqlite.org/backup.html
- S08 Android target 요구: https://developer.android.com/google/play/requirements/target-sdk
- S09 Apple 제출/향후요구: https://developer.apple.com/app-store/submitting/ ; https://developer.apple.com/news/upcoming-requirements/
- S10 Android16KB: https://developer.android.com/guide/practices/page-sizes
- S11 Godot CLI: https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- S12 Godot C# 플랫폼지원: https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/index.html
- S13 Apple 사용자프라이버시: https://developer.apple.com/app-store/user-privacy-and-data-use/
- S14 AdMob SSV: https://developers.google.com/admob/android/ssv ; D1: https://developers.cloudflare.com/d1/
- S15 Firebase Unity: https://firebase.google.com/docs/unity/setup
- S16 Unity2DAnimation/SpriteSkin: https://docs.unity3d.com/Packages/com.unity.2d.animation@10.0/manual/SpriteSkin.html
- S17 UnityNewtonsoft JSON: https://docs.unity3d.com/Packages/com.unity.nuget.newtonsoft-json@3.2/manual/index.html

라이선스적합성·법적적합성·광고수익은위출처몇개로보장하지않는다.소유자의실제계정/대상사용자/제출시점설정을검토한다.
