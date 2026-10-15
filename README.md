# Architect 지정 영상 일별 모니터링

YouTube 8개 및 Facebook 2개 영상의 공개 수치를 표시하는 GitHub Pages 대시보드입니다. 기존 화면과 영상별 행 × 날짜별 열의 기록 표, 조회수·좋아요·댓글·Facebook 반응 선택, CSV·JSON 내보내기를 제공합니다.

## 게시

1. 이 프로젝트를 전용 GitHub 저장소에 올립니다.
2. 저장소 **Settings → Pages → Build and deployment**에서 **Deploy from a branch**, **main**, **/docs**를 선택합니다.
3. GitHub가 제공한 Pages 주소로 접속합니다. 별도 서버 설치 없이 `docs`의 완성된 빌드를 게시할 수 있습니다.

`docs/.nojekyll`이 포함되어 있습니다. 상대 경로를 사용하므로 저장소 이름이나 하위 경로가 달라져도 동작합니다. Pages에 공개하는 파일은 웹에서 접근 가능하므로 접근 토큰이나 내부 운영 자료를 넣지 않습니다.

## 일일 자료 반영 구조

기존 수집 작업은 지정된 10개 영상만 확인하고 기존 데이터 저장소에 실제 관측 시각과 미확인 값을 보관합니다. 수집 후 검증된 자료를 이 저장소의 **`docs/data/observations.json`** 한 파일에 동기화하면 Pages에도 반영됩니다. 페이지를 열거나 새로고침해도 유료 수집을 실행하지 않습니다.

기존 일일 수집 작업에서 `sgtherong/architect-monitor`의 `main` 브랜치로 관측 파일을 동기화합니다. 수집 일정은 기존 작업 하나로 운영하며, GitHub 게시를 위한 중복 유료 조회를 실행하지 않습니다.

- 수집 범위: `data/targets.json`의 10개 ID만 허용합니다.
- 날짜 기준: Asia/Seoul. `observedAt`의 실제 시각을 보존합니다.
- 미확인: 숫자 0으로 채우지 않고 `null`로 유지합니다.
- 같은 날짜: 마지막 확인값을 표시합니다. 원본 관측 이력은 삭제하지 않습니다.
- 증감: 바로 전날 누적값과의 차이. 전날 값이 없으면 계산하지 않습니다.
- Facebook: 축약 표시된 조회수에는 `precision: "approximate"`를 보존합니다. 반응과 좋아요는 분리합니다.
- 채팅·감성 분석: 2026-10-13 기존 보고서의 고정 표본이며 일일 신규 분석이 아닙니다.

## 수집 작업에 추가할 동기화 절차

`COLLECTOR_SYNC.md`는 이 저장소에 연결된 수집 작업의 동기화 절차입니다. GitHub 연결 실패가 발생해도 기존 수집 데이터는 유지합니다. GitHub 동기화 성공은 파일을 다시 읽어 검증한 뒤 보고합니다.

## 로컬 개발 및 빌드

Node.js 22.13 이상이 필요합니다.

```sh
npm install
npm run build
```

`npm run build`는 `docs/data/observations.json`을 보존합니다. 데이터를 교체하지 않으며 `docs`에 앱 파일을 빌드합니다. `npm run dev`는 UI 개발용입니다. 실제 관측 파일을 포함한 결과는 빌드 후 `npm run preview`로 확인합니다.

기존 서버에서 내보낸 자료를 안전한 공개 파일로 변환할 때:

```sh
node scripts/prepare-snapshot.mjs /path/to/export.json
```

변환기는 지정 영상 ID, 숫자, 중복 관측, 한국 시간 날짜를 확인하고 운영 예산·인증 정보·설정의 불필요한 항목을 제외합니다. 이 스크립트는 영상 데이터를 새로 조회하지 않습니다.

## 파일 구성

- `app/`: React 화면과 스타일
- `data/`: 지정 영상, 배포 시점 예비 기록, 기존 반응 분석
- `docs/`: GitHub Pages 게시 파일
- `docs/data/observations.json`: 일일 갱신 대상
- `scripts/prepare-snapshot.mjs`: 공개 자료 검증 및 변환

인증 토큰, 비공개 수집 API, 데이터 입력·설정 변경 API는 이 저장소에 포함하지 않습니다.

2026-10-15 추가: JJAMx Gaming & Cosplay의 Facebook 영상 `1443913631040943`, PuddingKat CH의 YouTube 영상 `G36iQinLR0I`. 두 영상의 이전 날짜 수치는 소급 수집하지 않으며, 기존 채팅·감성 분석에 포함된 것으로 표시하지 않습니다.
