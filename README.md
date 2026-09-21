# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 목표와 현재 상태
Astra로 **시골 마을 v1.0을 광고 수익화까지 포함한 완결된 모바일 게임**으로 만든다.
고양이50종/최대50마리, 네 발 고양이의 실제 근무·야외 생활, 직접 돌봄→자동화가 핵심이다.
지역 이동과 후속 지역은 현재 범위 밖. 컨셉 LOCKED, 상세기획·검증 진행 중.

- 첫30분 분할지원/초기8마리와50개 실행가능 발견조건을 정의했다.
- 통합 v0.2는13개 시나리오/38개 계약·이벤트 검사를 실행했다.1개는 추가조건 제거 대조군이다.
- 저장·정산·광고 v0.1 명세와51개 참고 계약/로컬SQLite 예외경계 테스트를 추가했다.
- **게임 엔진·실기기·실제 광고SDK·SSV서버·저장 어댑터·스토어 출시·아트 제작은 완료가 아니다.**
- 후반 신규고양이 공백은 미해결 밸런스 항목. 모형 결과는 실제 사람의 완주일수나 출시품질이 아니다.

## 최신 문서 읽는 순서
1. [컨셉 기준선](docs/00_CONCEPT_LOCK.md)
2. [주민 정체성](docs/06_RESIDENT_SIMULATION.md) / [성장](docs/07_RESIDENT_GROWTH.md) / [생활](docs/11_LIFE_AI_AND_RELATIONSHIPS.md)
3. [건물](docs/16_BUILDING_LEVEL_SPEC.md) / [아트](docs/19_ART_DIRECTION.md)
4. [진행](docs/31_PROGRESSION_DATA_SPEC.md) / [경제](docs/33_ECONOMY_BALANCE_V01.md)
5. [정적 경제 검사](docs/34_ECONOMY_VALIDATION_REPORT.md) / [과거 대체구조 모형](docs/35_PROGRESSION_SIMULATION_V01.md)
6. [첫30분](docs/36_FIRST_30_MINUTES.md)
7. [발견조건](docs/37_DISCOVERY_RULES_V01.md) / [검증](docs/38_DISCOVERY_VALIDATION_V01.md)
8. [통합 진행·후반 공백](docs/39_INTEGRATED_PROGRESSION_V02.md) / [통합검사](docs/40_INTEGRATED_VALIDATION_REPORT.md)
9. **[저장·복구](docs/41_SAVE_AND_RECOVERY_CONTRACT.md)**
10. **[오프라인 정산](docs/42_OFFLINE_SETTLEMENT_CONTRACT.md)**
11. **[광고 보상·중단·증거복구](docs/43_REWARDED_AD_TRANSACTION.md)**
12. **[참고 저장검사 결과·한계](docs/44_PERSISTENCE_VALIDATION_REPORT.md)**

## 데이터 적용 순서
- [cats](data/cats.json): ID·성격·기본능력·외형. 상세 아트 필드 추가 필요.
- [buildings](data/buildings.json):13종. 과거 주민회관/여관 후보 사용하지 않음.
- [progression](data/progression.json) / [development](data/development_score.json):정원·발전도. 과거50/3,000/3,500점수는 대체됨.
- [economy](data/economy_balance.json):기본 수익·가격·광고·숙련 수치 초안.
- [onboarding](data/onboarding.json):최초1,000G + 추가600/2,900/1,000G 한 번씩. 총5,500G이며 중복지급하지 않음.
- [discovery](data/discovery_rules.json):cats.primaryCondition은 설명, 실제조건은 이 파일.
- [rescue timing](data/rescue_timing.json):정상42마리 시간 초안. 첫8마리는 onboarding 우선.
- [통합 시나리오](data/integrated_simulation_scenarios.json) / [결과요약](reports/integrated_progression_v02.summary.json)
- **[persistence contract](data/persistence_contract.json)** / [51개 검사결과](reports/persistence_validation_v01.json)

이번 저장 명세는 기존 경제·진행·발견·초기지원금을 바꾸지 않는다. 센터10 240만G는 과거 비교실험이며 기본320만G를 대체하지 않는다.
광고중 자연완료된 단축대상에 대한 대체골드는 신규 상세 초안으로 장기시뮬레이션에는 아직 반영하지 않았다.
캐릭터 시트 docs/21~26의 개성은 유지하되 밤/비/관계가 필수라는 구 예시보다37번 조건식을 우선한다.

## 검증
```sh
python3 -S tools/validate_balance.py
python3 -S tools/test_onboarding_contract.py
python3 -S tools/validate_discovery.py
python3 -S tools/test_discovery_contract.py
python3 -S tools/simulate_integrated_progression.py --include-events
python3 -S tools/test_integrated_progression.py
```
통합 검사는 전체이벤트 결과가 있으면38개, 없으면 결과검사6개를 스킵한다. 이전 고정입력 투영은 대화 ZIP에 있으며 data/에 덮어쓰지 않는다.
신규 저장검사51개는 독립 참고모형으로 실행했다. Python 실행기 업로드는 연결 도구에서 차단되어 이번 Git에는 명세·계약·결과만 기록한다. 실행기와 테스트 원문은 대화 ZIP에 있다. 해당 소스가 있는 별도 작업 폴더에서 `python3 -S tools/test_persistence_contract.py`로 재현한다. 원래 전체시뮬레이터나 Unity/Godot 런타임을 재실행한 결과가 아니다.
SQLite는 시험용 선택이며 엔진/저장 라이브러리를 확정한 것이 아니다. 서버서명·실광고·OS강제종료·백업복원·migration은 별도 구현/시험이 필요하다.

다음: 엔진·광고·저장 어댑터/에셋 제작 흐름과 Astra 구현 명세 선택. 내부 첫1마리 관통 시험 후50마리 완결형 출시로 이어간다.
