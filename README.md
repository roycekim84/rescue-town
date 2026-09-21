# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 목표
Astra로 **시골 마을 v1.0을 광고 수익화까지 포함한 완결된 모바일 게임**으로 만든다.
고양이 50종/최대50마리, 네 발 고양이의 실제 건물 근무와 야외 생활, 직접 돌봄→자동화가 핵심이다.
지역 이동과 후속 지역의 상세 기획/구현은 현재 범위 밖이다.

## 현재 상태
- 컨셉: LOCKED.
- 상세기획: 진행 중.
- 경제: v0.1 수치 초안/정적 검증 + 가정 기반 진행 시뮬레이션 1차. 실제 이용자 완주 기간·출시 밸런스는 미확정.
- 런타임·실기기 광고·스토어 출시 완료 상태가 아니다.
- 현재 작업은 기획/데이터다. 승인 없이 새 지역이나 실제 아트 에셋을 생성하지 않는다.

## 최신 문서 읽는 순서
1. [컨셉 기준선](docs/00_CONCEPT_LOCK.md)
2. [주민 정체성과 실제 생활](docs/06_RESIDENT_SIMULATION.md)
3. [주민 성장](docs/07_RESIDENT_GROWTH.md) / [생활 AI·관계](docs/11_LIFE_AI_AND_RELATIONSHIPS.md)
4. [건물 레벨 명세](docs/16_BUILDING_LEVEL_SPEC.md) / [아트 규칙](docs/19_ART_DIRECTION.md)
5. [진행 데이터 명세](docs/31_PROGRESSION_DATA_SPEC.md)
6. [경제 수치 초안](docs/33_ECONOMY_BALANCE_V01.md)
7. [경제·진행 정적 검증](docs/34_ECONOMY_VALIDATION_REPORT.md)
8. [진행 시뮬레이션 결과·가정·남은 과제](docs/35_PROGRESSION_SIMULATION_V01.md)

기존 문서의 예시 숫자와 최신 JSON이 충돌하면 최신 명세/JSON을 기준으로 한다.
특히 과거 발전도50/3,000/3,500 등은 검증 후 수정되었으므로 구현에 복사하지 않는다.
예전 14종 건물/주민회관/여관 후보 대신 현재 buildings.json의13종을 사용한다.

## 데이터
- [고양이50마리](data/cats.json): 상세 발견 조건/외형 필드 보강이 남은 초안.
- [건물13종](data/buildings.json)
- [센터 진행](data/progression.json)
- [발전도](data/development_score.json)
- [경제·광고 수치](data/economy_balance.json)
- [시뮬레이션 가정 및 비교안](data/simulation_scenarios.json)
- [실행 결과 요약](reports/progression_simulation_v01.summary.json)

가격·시간·광고 배율·숙련곡선은 기획 초안이며 데이터 버전으로 관리한다.
`docs/21`부터 `docs/26`까지의 캐릭터 시트는 도감 콘텐츠의 상세 참고 자료다.
시뮬레이션의 초기5,500G는 비교 실험일 뿐, 실제 경제 기본값1,000G를 변경하지 않았다.

## 검증
```sh
python3 -S tools/validate_balance.py
```
Python 표준 라이브러리만 사용한다. 이 검사 통과는 게임 완성이나 SDK/완주 테스트 통과를 의미하지 않는다.

진행 모형은7개 시나리오를 실행하고 별도 단위테스트14개를 통과했다. 개별 구조조건은 아직 대체 타이머이므로 실제50마리 전체 획득 경로 검증은 아니다.
**시뮬레이션 실행기 소스의 Git 업로드가 연결 도구에서 차단되어, 실행기와 테스트는 이번 대화의 별도 ZIP으로 제공한다. 현재 저장소에는 설정·결과·해석 문서만 추가되어 있다.**
ZIP의 축약 입력을 실제 게임 데이터에 덮어쓰지 않는다. 자세한 재현 방법과 한계는35번 문서를 참고한다.

다음 작업은 첫30분의 골드 지급/첫 경제시설 체험을 구체화하고,50마리 실제 발견조건을 실행 가능한 데이터로 연결해 진행을 다시 검증하는 것이다.
