# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 지금 시작할 곳
**기획 인계와 Astra 구현 작업서 준비 완료. 다음 작업은 M0 환경 확인과 Unity 프로젝트 생성이다.**
실제 게임 구현·아트 생산·모바일 광고 연동·서버 배포·스토어 출시는 아직 완료되지 않았다.

- [Astra 첫 구현 프롬프트](prompts/ASTRA_START.md)
- [총괄 구현 작업서 M0~M7](docs/47_ASTRA_IMPLEMENTATION_WORKBOOK.md)
- [기술 선택: Unity·광고·SQLite·영수증 서비스](docs/45_TECH_STACK_DECISIONS.md)
- [최신 사양 우선순위·이전 초안 대체·공식 근거](docs/49_SPEC_AUTHORITY_AND_HANDOFF.md)
- [출시 인수 기준](docs/48_RELEASE_ACCEPTANCE.md)
- [현재 구현 상태](docs/50_IMPLEMENTATION_STATUS.md) / [기계판독 작업 계획](data/implementation_plan.json)

## v1.0 목표
시골마을 하나, 고양이50종/최대50마리, 건물13종, 네 발 고양이의 실제 근무와 생활, 직접 돌봄에서 자동화로 성장하는 완결된 모바일 게임이다.
건물별 직원은 최대3마리이며 희귀도·캐릭터레벨은 없다. 고유 기본능력과 근무 숙련으로 키운다.
광고를 실제로 붙여 출시하되 광고 없이도 모든 핵심 콘텐츠와50마리 수집에 접근할 수 있어야 한다.
지역 이동·후속맵·프레스티지·IAP·PvP는 현재 출시 범위 밖이다. 첫 한마리 관통 시험은 내부 개발 순서이며 작은 MVP만 출시하는 것이 아니다.

## 선정한 구현 방향
Unity6.3 LTS / C# / 2D URP / uGUI·TMP / SQLite / Google Mobile Ads·UMP / 최소 SSV Worker·D1.
선정은 설치·호환검증 완료를 뜻하지 않는다. 정확한 에디터 패치와 패키지 잠금은 M0에서 실제 환경으로 확정한다.
기본 광고는 보상형이며 강제 전면·배너·앱실행광고는 꺼둔다. 로컬 저장과 서버 영수증은 클라우드 마을 저장이 아니다.
[46번 구현 기본값](docs/46_RUNTIME_AND_ASSET_BASELINE.md)에 지정 필지, 주택 정원, 아트·UI·꾸미기 제작 범위를 정리했다. 실제 이미지나 Unity 프로젝트를 이번 인계에서 생성한 것은 아니다.

## 게임 데이터 원본
| 파일 | 의미 |
|---|---|
| [cats.json](data/cats.json) |50개 고유ID·기본능력·성격·외형 초안 |
| [buildings.json](data/buildings.json) |13종·5/10레벨·직원슬롯·역할 |
| [progression.json](data/progression.json) |센터1~10·정원·발전도·축제조건 |
| [development_score.json](data/development_score.json) |종류별 최고 완료레벨 집계 |
| [economy_balance.json](data/economy_balance.json) |가격·수익·경험·광고 수치 초안 |
| [onboarding.json](data/onboarding.json) |첫8마리·분할지원·첫 영업 |
| [discovery_rules.json](data/discovery_rules.json) |50마리의 실행 가능한 조건식 |
| [rescue_timing.json](data/rescue_timing.json) |정상42마리의 탐색·돌봄 시간 |
| [persistence_contract.json](data/persistence_contract.json) |저장·정산·보상 계약 |

초기자금은 최초1,000G + 추가600/2,900/1,000G를 한 번씩 지급하여 총5,500G다. 과거 최초5,500G 실험에 추가4,500G를 중복 적용하지 않는다.
cats.primaryCondition은 설명 라벨이며 실행 조건은 discovery_rules다. home/square 선호별칭은 정규화한다.
과거 문서의 주민회관/여관/14종, 발전도3,000/3,500, 보유30마리 예시보다 [49번 우선순위](docs/49_SPEC_AUTHORITY_AND_HANDOFF.md)를 따른다.

## 주요 기획·검증 문서
[컨셉](docs/00_CONCEPT_LOCK.md) · [주민 정체성](docs/06_RESIDENT_SIMULATION.md) · [성장](docs/07_RESIDENT_GROWTH.md) · [생활·관계](docs/11_LIFE_AI_AND_RELATIONSHIPS.md) · [건물](docs/16_BUILDING_LEVEL_SPEC.md) · [아트](docs/19_ART_DIRECTION.md).

[경제](docs/33_ECONOMY_BALANCE_V01.md) · [첫30분](docs/36_FIRST_30_MINUTES.md) · [발견조건](docs/37_DISCOVERY_RULES_V01.md) · [발견검증](docs/38_DISCOVERY_VALIDATION_V01.md) · [통합진행](docs/39_INTEGRATED_PROGRESSION_V02.md) · [통합검증](docs/40_INTEGRATED_VALIDATION_REPORT.md).

[저장·복구](docs/41_SAVE_AND_RECOVERY_CONTRACT.md) · [오프라인](docs/42_OFFLINE_SETTLEMENT_CONTRACT.md) · [광고보상](docs/43_REWARDED_AD_TRANSACTION.md) · [참고 저장검사](docs/44_PERSISTENCE_VALIDATION_REPORT.md).

## 검증을 실행할 때
```sh
python3 -S tools/validate_balance.py
python3 -S tools/test_onboarding_contract.py
python3 -S tools/validate_discovery.py
python3 -S tools/test_discovery_contract.py
python3 -S tools/simulate_integrated_progression.py --include-events
python3 -S tools/test_integrated_progression.py
```
현재 저장소의 실제 입력으로 실행하고 성공·실패·스킵을 기록한다. 과거 수치모형과 로컬 참고검사는 Unity/실광고/모바일 강제종료 통과 증거가 아니다.
과거 통합모형은13개 시나리오/38개 검사를 보고했다. 전체 이벤트 결과가 없으면 재생검사 일부는 스킵된다. 이전 snapshot은 검증 당시 필드 투영이며 게임 data/를 덮어쓰면 안 된다.
51개 저장 참고검사 보고서는 있으나 당시 Python 원문은 Git 업로드가 차단되어 이 저장소에 없다. 같은 검사를 수행했다고 가장하지 말고 계약에 맞는 C# 테스트를 구현한다.
이번 인계 검사는 [manifest 검사](reports/handoff_manifest_check.json)만 실행했다. Unity나 장기 시뮬레이터를 다시 실행하지 않았다.

## 미해결 사항
후반 신규고양이 사이 공백, 전체 아트·방향별 정체성, 주택/꾸미기 포함 재밸런스, 네이티브 패키지 호환, 실기기 저장·광고/SSV는 개발·출시 게이트에 남아 있다. 센터10 비용240만G는 과거 비교안이며 기본320만G를 대체하지 않았다.
계정·비밀·서명·공개배포·스토어 제출은 소유자 승인 후 진행한다. 설정 누락은 차단으로 남기고 임의로 완료 처리하지 않는다.

**다음 실행: `prompts/ASTRA_START.md`로 M0를 시작하고, 통과 후 M1로 이어간다.**
