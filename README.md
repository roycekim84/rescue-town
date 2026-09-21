# Rescue Town

> 구조한 고양이들이 주민이 되고, 주민들이 스스로 살아가며 성장시키는 작은 시골 마을.

## 목표
Astra로 **시골 마을 v1.0을 광고 수익화까지 포함한 완결된 모바일 게임**으로 만든다.
고양이 50종/최대50마리, 네 발 고양이의 실제 건물 근무와 야외 생활, 직접 돌봄→자동화가 핵심이다.
지역 이동과 후속 지역의 상세 기획/구현은 현재 범위 밖이다.

## 현재 상태
- 컨셉: LOCKED.
- 상세기획: 진행 중.
- 경제: v0.1 수치 초안/진행 도달 가능성 정적 검증. 출시 밸런스·완주 기간은 미검증.
- 런타임·실기기 광고·스토어 출시 완료 상태가 아니다.
- 현재 작업은 기획/데이터다. 승인 없이 새 지역이나 실제 아트 에셋을 생성하지 않는다.

## 최신 문서 읽는 순서
1. [컨셉 기준선](docs/00_CONCEPT_LOCK.md)
2. [주민 정체성과 실제 생활](docs/06_RESIDENT_SIMULATION.md)
3. [주민 성장](docs/07_RESIDENT_GROWTH.md) / [생활 AI·관계](docs/11_LIFE_AI_AND_RELATIONSHIPS.md)
4. [건물 레벨 명세](docs/16_BUILDING_LEVEL_SPEC.md) / [아트 규칙](docs/19_ART_DIRECTION.md)
5. [진행 데이터 명세](docs/31_PROGRESSION_DATA_SPEC.md)
6. [경제 수치 초안](docs/33_ECONOMY_BALANCE_V01.md)
7. [경제·진행 검증 및 남은 과제](docs/34_ECONOMY_VALIDATION_REPORT.md)

기존 문서의 예시 숫자와 최신 JSON이 충돌하면 최신 명세/JSON을 기준으로 한다.
특히 과거 발전도50/3,000/3,500 등은 검증 후 수정되었으므로 구현에 복사하지 않는다.
예전 14종 건물/주민회관/여관 후보 대신 현재 buildings.json의13종을 사용한다.

## 데이터
- [고양이50마리](data/cats.json): 상세 발견 조건/외형 필드 보강이 남은 초안.
- [건물13종](data/buildings.json)
- [센터 진행](data/progression.json)
- [발전도](data/development_score.json)
- [경제·광고 수치](data/economy_balance.json)

가격·시간·광고 배율·숙련곡선은 기획 초안이며 데이터 버전으로 관리한다.
`docs/21`부터 `docs/26`까지의 캐릭터 시트는 도감 콘텐츠의 상세 참고 자료다.

## 검증
```sh
python3 -S tools/validate_balance.py
```
Python 표준 라이브러리만 사용한다. 이 검사 통과는 게임 완성이나 SDK/완주 테스트 통과를 의미하지 않는다.
다음 작업은 실제 업그레이드 선택·접속·발견 조건을 반영한 진행/경제 시뮬레이션이다.
