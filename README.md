# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 목표와 현재 상태
Astra로 **시골 마을 v1.0을 광고 수익화까지 포함한 완결된 모바일 게임**으로 만든다.
고양이50종/최대50마리, 네 발 고양이의 실제 건물 근무와 야외 생활, 직접 돌봄→자동화가 핵심이다.
지역 이동과 후속 지역 상세기획/구현은 현재 범위 밖이다. 컨셉은 LOCKED이며 상세기획/검증은 진행 중이다.

- 첫30분 분할지원/초기8마리/실제 영업 시작을 통합했다.
- 실제50개 발견조건·경제·숙련·정원·광고를 함께 계산한 v0.2 모형13개 시나리오와38개 계약/이벤트 재생 검사 통과. 1개 시나리오는 추가 발견조건 제거 대조군이다.
- 후반 새 고양이를 만나지 못하는 공백은 미해결 밸런스 항목이다. 시뮬레이션 결과를 실제 사람의 완주일수나 출시품질로 해석하지 않는다.
- 게임 런타임,실기기,광고SDK,스토어 출시,실제 아트는 아직 완료가 아니다. 지금은 기획/데이터 작업이다.

## 최신 문서 읽는 순서
1. [컨셉 기준선](docs/00_CONCEPT_LOCK.md)
2. [주민 정체성](docs/06_RESIDENT_SIMULATION.md)
3. [성장](docs/07_RESIDENT_GROWTH.md) / [생활·관계](docs/11_LIFE_AI_AND_RELATIONSHIPS.md)
4. [건물 레벨](docs/16_BUILDING_LEVEL_SPEC.md) / [아트 규칙](docs/19_ART_DIRECTION.md)
5. [진행 데이터](docs/31_PROGRESSION_DATA_SPEC.md) / [경제 기준](docs/33_ECONOMY_BALANCE_V01.md)
6. [정적 경제 검사](docs/34_ECONOMY_VALIDATION_REPORT.md) / [과거 대체구조 모형](docs/35_PROGRESSION_SIMULATION_V01.md)
7. [첫30분](docs/36_FIRST_30_MINUTES.md)
8. [50마리 발견 조건](docs/37_DISCOVERY_RULES_V01.md) / [구조적 검사](docs/38_DISCOVERY_VALIDATION_V01.md)
9. **[통합 진행 v0.2 결과·후반 공백](docs/39_INTEGRATED_PROGRESSION_V02.md)**
10. **[통합 검사·재현·한계](docs/40_INTEGRATED_VALIDATION_REPORT.md)**

## 데이터 적용 순서
- [cats](data/cats.json): ID·성격·기본능력·외형 원본. 상세 아트 제작 명세는 추가 필요.
- [buildings](data/buildings.json):13종. 과거 주민회관/여관/14종 후보를 사용하지 않는다.
- [progression](data/progression.json) / [development](data/development_score.json):센터 정원/발전도. 과거50/3,000/3,500 점수는 대체되었다.
- [economy](data/economy_balance.json):기본 수익·가격·광고·숙련 초안.
- [onboarding](data/onboarding.json):첫8마리와 초기 제한,최초1,000G에 추가600/2,900/1,000G를 한 번씩 지급. 총5,500G이며 최초5,500+추가4,500으로 중복 지급하지 않는다.
- [discovery](data/discovery_rules.json):실제 발견 조건. cats.primaryCondition은 설명 문자열이며 실행하지 않는다.
- [rescue timing](data/rescue_timing.json):정상42마리 시간 초안. 첫8마리는 onboarding을 우선한다. 최소 발견센터 기준이며 현재센터 상승으로 옛 고양이 시간이 늘지 않는다.
- [v0.2 실험 설정](data/integrated_simulation_scenarios.json) / [결과요약](reports/integrated_progression_v02.summary.json)

원본 경제/발견/센터/지원금은 이번에 변경하지 않았다. 센터10 240만G는 비교 시나리오이며 기본320만G를 대체하지 않는다.
정상 타이머도 출시 확정이 아닌 실험 초안이다. 이전 완주일수를 다른 정책의 결과로 재사용하지 않는다.
캐릭터 시트 docs/21~26의 개성은 유지하되 밤/비/관계가 필수라는 구 예시보다37번 조건식을 우선한다.

## 검증 및 재현
```sh
python3 -S tools/validate_balance.py
python3 -S tools/test_onboarding_contract.py
python3 -S tools/validate_discovery.py
python3 -S tools/test_discovery_contract.py
python3 -S tools/simulate_integrated_progression.py --include-events
python3 -S tools/test_integrated_progression.py
```

새 통합 실행기·공통경제모형·테스트는 tools/에 있다. 기존 v0.1 실행기 업로드 차단에 대한 과거 기록과 구분한다.
로컬 실행은 이전에 검증한 계산 필드 투영을 사용했다. 당시 고정입력과 전체 이벤트 결과는 대화 ZIP에 보존하며,게임 data/를 덮어쓰지 않는다.
--snapshot 재현에는 ZIP의 reports/integrated_source_projection.json이 필요하다. 기본 명령은 저장소의 실제 data/를 읽는다.
전체 시뮬레이션 --include-events 실행 후 계약32개+결과검사6개=38개를 검사한다. 아직 결과가 없으면6개는 스킵된다.
SDK/저장 원자성/실기기/재미는 이 테스트 범위가 아니다.

다음 상세기획: 저장 스키마·오프라인 정산·지원/광고 보상 고유ID·중단 복귀. 후반 수집 공백은 추후 플레이테스트의 우선 밸런스 항목으로 유지한다.
