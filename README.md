# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 목표
Astra로 **시골 마을 v1.0을 광고 수익화까지 포함한 완결된 모바일 게임**으로 만든다.
고양이50종/최대50마리, 네 발 고양이의 실제 건물 근무와 야외 생활, 직접 돌봄→자동화가 핵심이다.
지역 이동과 후속 지역의 상세 기획/구현은 현재 범위 밖이다.

## 현재 상태
- 컨셉: LOCKED. 상세기획·데이터: 진행 중.
- 경제: v0.1 정적 검증 및 가정 기반 진행 모형. 출시 밸런스·실제 완주 기간 미확정.
- 첫30분: 분할 지원금·첫8마리·첫 생산시설을 명세화하고 참조모형18개 검사 통과.
- 발견: 50개 실행 가능한 조건식, 참조모형28개 테스트 통과. 무작위 수집 순서와 정원에 대한 구조적 경로 검사 완료. 최신 조건을 포함한 전체 소요시간은 미검증.
- 런타임·실기기 광고·스토어 출시 완료 상태가 아니다.
- 현재는 기획/데이터 작업이며 새 지역이나 실제 아트 에셋을 생성하지 않는다.

## 최신 문서 읽는 순서
1. [컨셉 기준선](docs/00_CONCEPT_LOCK.md)
2. [주민 정체성](docs/06_RESIDENT_SIMULATION.md)
3. [주민 성장](docs/07_RESIDENT_GROWTH.md) / [생활 AI·관계](docs/11_LIFE_AI_AND_RELATIONSHIPS.md)
4. [건물 레벨](docs/16_BUILDING_LEVEL_SPEC.md) / [아트 규칙](docs/19_ART_DIRECTION.md)
5. [진행 데이터](docs/31_PROGRESSION_DATA_SPEC.md)
6. [경제 수치 초안](docs/33_ECONOMY_BALANCE_V01.md)
7. [경제·진행 정적 검증](docs/34_ECONOMY_VALIDATION_REPORT.md)
8. [이전 진행 시뮬레이션과 한계](docs/35_PROGRESSION_SIMULATION_V01.md)
9. [첫30분·분할 지원금·중단 복귀](docs/36_FIRST_30_MINUTES.md)
10. [50마리 발견 조건·선택·정원 계약](docs/37_DISCOVERY_RULES_V01.md)
11. [발견 조건 검증 결과와 한계](docs/38_DISCOVERY_VALIDATION_V01.md)

## 데이터 적용 순서
- [cats.json](data/cats.json): 50마리 ID·기본능력·성격·외형의 원본. 상세 아트 필드는 추가 제작 명세가 필요하다.
- [buildings.json](data/buildings.json): 건물13종.
- [progression.json](data/progression.json) / [development_score.json](data/development_score.json): 센터 정원과 발전도.
- [economy_balance.json](data/economy_balance.json): 경제·광고 수치 초안.
- [onboarding.json](data/onboarding.json): 기본 경제 위의 일회성 지원·첫8마리·UI 공개 규칙.
- [discovery_rules.json](data/discovery_rules.json): catalogId로 조인하는50마리 실제 조건식. 첫8개 조건은 onboarding과 일치해야 한다.
- [이전 시뮬레이션 설정](data/simulation_scenarios.json) / [이전 결과](reports/progression_simulation_v01.summary.json)
- [초기 검증](reports/onboarding_validation_v01.json) / [발견 조건 검증](reports/discovery_validation_v01.json)

과거 대화·문서의 예시 숫자보다 최신 명세/JSON을 우선한다. 발전도50/3,000/3,500, 주민회관/여관 후보를 복사하지 않는다.
현재 건물은13종이며 보유상한은50마리다. 캐릭터 시트 docs/21~26의 개성은 유지하되 미확정 밤/비/관계 출현 예시는37번 조건식보다 우선하지 않는다.
`cats.discovery.primaryCondition`은 설명 라벨이며 실행 조건이 아니다. 이를 직접 해석하는 임의 코드를 추가하지 않는다.

### 최초 자금
시작1,000G + 조건부 지원600/2,900/1,000G를 한 번씩 지급하는 안이다. 총5,500G에 최초1,000G가 포함된다.
이전35번의 최초5,500G 실험은 다른 정책이다. 그 완주 일수를 분할지원/신규 발견조건의 결과로 재사용하지 않는다.

## 검증
```sh
python3 -S tools/validate_balance.py
python3 -S tools/test_onboarding_contract.py
python3 -S tools/validate_discovery.py
python3 -S tools/test_discovery_contract.py
```

현재 저장소 전체 입력 대신 검증 당시 필드 투영을 사용할 때:
```sh
python3 -S tools/test_onboarding_contract.py --snapshot
python3 -S tools/validate_discovery.py --snapshot
python3 -S tools/test_discovery_contract.py --snapshot
```

이번 로컬 발견 검사는 --snapshot으로 실행했다. 100개 난수시드와2개 수집정책을 초기시설 표기2종으로 반복한400회 구조적 검사이며, 실제 인간 플레이400개나 완주 속도 검증이 아니다.
투영 입력은 reports/에만 두고 게임 data/에 덮어쓰지 않는다. 참조 reducer의 체크포인트 검사는 실제 기기의 원자적 저장/강제종료를 대신하지 않는다.
이전 장기 진행 모형은7개 시나리오/단위테스트14개를 실행했으나 당시 실행기 Git 업로드가 차단되어 소스는 이전 대화 ZIP에 있다. 이번 조건 검사기는 그 실행기와 별개이며 저장소 tools/에 포함되어 있다.

다음: 분할 지원금 + 50마리 실제 발견조건 + 정상 탐색/돌봄 타이머를 장기 진행 모형에 통합해 재검증.
