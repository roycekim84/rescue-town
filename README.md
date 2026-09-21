# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 목표
Astra로 **시골 마을 v1.0을 광고 수익화까지 포함한 완결된 모바일 게임**으로 만든다.
고양이50종/최대50마리, 네 발 고양이의 실제 건물 근무와 야외 생활, 직접 돌봄→자동화가 핵심이다.
지역 이동과 후속 지역의 상세 기획/구현은 현재 범위 밖이다.

## 현재 상태
- 컨셉: LOCKED. 상세기획·데이터: 진행 중.
- 경제: v0.1 정적 검증 및 가정 기반 진행 모형. 출시 밸런스·실제 완주 기간 미확정.
- 첫30분: 단계별 지원금·첫8마리·첫 생산시설 선택을 명세화하고 데이터/참조모형18개 검사 통과.
- 런타임·실기기 광고·스토어 출시 완료 상태가 아니다.
- 현재는 기획/데이터 작업이다. 새 지역이나 실제 아트 에셋을 생성하지 않는다.

## 최신 문서 읽는 순서
1. [컨셉 기준선](docs/00_CONCEPT_LOCK.md)
2. [주민 정체성](docs/06_RESIDENT_SIMULATION.md)
3. [주민 성장](docs/07_RESIDENT_GROWTH.md) / [생활 AI·관계](docs/11_LIFE_AI_AND_RELATIONSHIPS.md)
4. [건물 레벨](docs/16_BUILDING_LEVEL_SPEC.md) / [아트 규칙](docs/19_ART_DIRECTION.md)
5. [진행 데이터](docs/31_PROGRESSION_DATA_SPEC.md)
6. [경제 수치 초안](docs/33_ECONOMY_BALANCE_V01.md)
7. [경제·진행 정적 검증](docs/34_ECONOMY_VALIDATION_REPORT.md)
8. [이전 진행 시뮬레이션 결과와 한계](docs/35_PROGRESSION_SIMULATION_V01.md)
9. [첫30분 플레이·분할 지원금·중단 복귀 명세](docs/36_FIRST_30_MINUTES.md)

## 데이터 및 적용 순서
- [고양이50마리](data/cats.json): 상세 외형/발견조건 보강이 남은 초안.
- [건물13종](data/buildings.json)
- [센터 진행](data/progression.json) / [발전도](data/development_score.json)
- [경제·광고 수치](data/economy_balance.json)
- [첫30분 데이터](data/onboarding.json): 기본 경제 위의 일회성 지원·초기 발견·UI 공개 규칙.
- [이전 시뮬레이션 설정](data/simulation_scenarios.json) / [이전 결과](reports/progression_simulation_v01.summary.json)
- [첫30분 검증 결과](reports/onboarding_validation_v01.json)

기존 대화/문서의 예시 숫자보다 최신 명세/JSON을 우선한다. 과거 발전도50/3,000/3,500, 주민회관/여관 후보를 복사하지 않는다.
현재 건물은13종이며 첫 마을 보유상한은50마리다. 캐릭터 상세 시트는 docs/21~26을 참고한다.

### 첫 자금 해석 주의
`economy_balance.json`의 최초1,000G는 그대로다. 최신 첫30분 안은 여기에 조건부 지원600+2,900+1,000G를 **한 번씩** 추가한다.
총액5,500G에는 최초1,000G가 포함된다. 최초5,500G를 주고 추가4,500G를 또 지급하면 안 된다.
이전35번 문서의 최초5,500G 비교 실험은 다른 정책이다. 이번 분할지급안의 장기 완주를 검증한 결과로 재사용하지 않는다.
첫8마리의 구체적인 초기 출현은 onboarding.json을 우선하고, 첫 실제 영업 이후 나머지는 일반 발견 규칙을 따른다.
기본 경제파일만 읽으면 신규 단계 지원은 적용되지 않는다. Astra 런타임과 후속 시뮬레이터는 두 데이터의 연동을 구현해야 한다.

## 검증
```sh
python3 -S tools/validate_balance.py
python3 -S tools/test_onboarding_contract.py
python3 -S tools/test_onboarding_contract.py --snapshot
```
두 번째 명령은 현재 저장소 데이터를, 세 번째는 입력 커밋의 필요한 계산 필드만 담은 reports/onboarding_source_projection.json을 사용한다.
이번 로컬 실행은 --snapshot이며18개 테스트를 통과했다. 참고 모형의 지급 중복/체크포인트 복원은 실제 앱의 원자적 저장·강제종료 검증을 대신하지 않는다.
계산 필드 투영을 data/에 덮어쓰지 않는다. 실제 플레이20~30분과 전체50마리 경로는 아직 미검증이다.

이전 진행 모형은7개 시나리오/단위테스트14개를 실행했으나, **당시 실행기 Git 업로드가 차단되어 그 소스는 이전 대화 ZIP에만 있다.**
새로운 첫30분 계약 테스트는 그 실행기와 다른 작은 검사다. 기존 결과·기본 경제·센터 조건은 이번 작업에서 덮어쓰지 않는다.

다음: 나머지42마리의 실행 가능한 발견조건, 전체50마리의 순환잠금 검사, 분할지급 초기 흐름과 장기 진행 모형의 통합 검증.
