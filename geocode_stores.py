<!DOCTYPE html>
<html>
<head>
    <title>행정안전부 착한가격업소 지도</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script type="text/javascript" 
            src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=9b8113591f35c3409335bdb4b5ee5613&libraries=clusterer&autoload=false" 
            defer></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js"></script>
    <style>
        html, body { 
            margin: 0; 
            padding: 0; 
            height: 100%; 
            overflow: hidden; 
        }
        #logo { 
            text-align: center; 
            padding: 10px; 
            margin: 0; 
            position: fixed; 
            top: 0; 
            width: 100%; 
            z-index: 100; 
            background: rgba(255, 255, 255, 0.8); 
            cursor: pointer; /* 클릭 가능 표시 */
        }
        #logo img { 
            max-width: 300px; 
            height: auto; 
            vertical-align: middle; 
        }
        #map { 
            width: 100%; 
            height: 100%; 
            position: absolute; 
            top: 0; 
            z-index: 1; 
        }
        .info-window { 
            font-size: 12px; padding: 1px 2px; background: white; border: 1px solid #333; 
            border-radius: 3px; display: inline-block; white-space: nowrap; width: fit-content; 
            max-width: 200px; overflow: hidden; text-overflow: ellipsis; margin: 0; 
            box-sizing: content-box; position: relative; top: -35px; cursor: pointer;
        }
        .detail-window { 
            font-size: 14px; padding: 10px; background: white; border: 1px solid #666; 
            border-radius: 5px; max-width: 300px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); 
            line-height: 1.5; cursor: pointer;
        }
        .click-area { 
            width: 40px; height: 40px; background: transparent; border-radius: 50%; 
            position: absolute; top: -20px; left: -20px; cursor: pointer;
        }
        #dropdown-container { 
            position: fixed; 
            left: 50%; 
            transform: translateX(-50%); 
            top: 70px; /* 초기값, JS에서 동적 조정 */
            z-index: 100; 
            text-align: center; 
        }
        #region-select, #price-select { 
            display: inline-block; 
            padding: 5px; 
            font-size: 16px; 
            margin: 0 10px; /* 드롭다운 간 간격 */
        }
        #loading { 
            position: fixed; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%); 
            background: rgba(0,0,0,0.7); 
            color: white; 
            padding: 20px; 
            z-index: 200; 
            display: none; 
        }
        @media (max-width: 600px) { 
            #dropdown-container { 
                top: 60px; /* 모바일에서 로고 크기 조정 반영 */
            }
            #region-select, #price-select { 
                display: inline-block; /* 모바일에서도 좌우 배치 */
                width: 110px; /* 모바일에서 더 작은 너비 */
                margin: 0 5px; /* 모바일에서 간격 줄임 */
                font-size: 14px; 
            }
            #logo img { max-width: 200px; }
        }
    </style>
</head>
<body>
    <div id="logo">
        <img src="logo.png" alt="행정안전부 착한가격업소 로고">
    </div>
    <div id="map">
        <div id="dropdown-container">
            <select id="region-select">
                <option value="">지역을 선택하세요</option>
                <option value="서울" selected>서울</option>
                <option value="광주">광주</option>
                <option value="대구">대구</option>
                <option value="대전">대전</option>
                <option value="부산">부산</option>
                <option value="세종">세종</option>
                <option value="울산">울산</option>
                <option value="인천">인천</option>
                <option value="강원도">강원도</option>
                <option value="경기도">경기도</option>
                <option value="경상도">경상도</option>
                <option value="전라도">전라도</option>
                <option value="제주도">제주도</option>
                <option value="충청도">충청도</option>
            </select>
            <select id="price-select">
                <option value="">가격대를 선택하세요</option>
                <option value="10000+">10000원 이상</option>
                <option value="10000">10000원 이하</option>
                <option value="9000">9000원 이하</option>
                <option value="8000">8000원 이하</option>
                <option value="7000">7000원 이하</option>
                <option value="6000">6000원 이하</option>
                <option value="5000" selected>5000원 이하</option>
            </select>
        </div>
    </div>
    <div id="loading">지도 로딩 중...</div>
    <script>
        let map;
        let clusterer;
        let markers = [];
        let overlays = [];
        let clickAreas = [];
        let currentInfowindow = null;
        let currentRegion = "서울";
        let currentPriceRange = "5000";
        let allStores = [];
        let isLoadingMarkers = false;

        function adjustMapPosition() {
            const logo = document.getElementById('logo');
            const mapDiv = document.getElementById('map');
            const dropdownContainer = document.getElementById('dropdown-container');

            const logoHeight = logo.offsetHeight;
            dropdownContainer.style.top = `${logoHeight + 10}px`; // 로고 아래 여유 공간 10px
            mapDiv.style.top = `${logoHeight}px`;
            mapDiv.style.height = `calc(100% - ${logoHeight}px)`;
        }

        function resetToInitialState() {
            // 초기화: 서울, 5000원 이하
            currentRegion = "서울";
            currentPriceRange = "5000";
            
            // 드롭다운 메뉴 값 업데이트
            document.getElementById('region-select').value = "서울";
            document.getElementById('price-select').value = "5000";

            // 지도 로드
            loadStores(currentRegion, currentPriceRange);
        }

        function initMap() {
            const container = document.getElementById('map');
            if (!container) {
                console.error("❌ 지도 컨테이너 없음");
                return;
            }
            const options = {
                center: new kakao.maps.LatLng(37.5665, 126.9780),
                level: 8
            };
            map = new kakao.maps.Map(container, options);
            clusterer = new kakao.maps.MarkerClusterer({
                map: map,
                averageCenter: true,
                minLevel: 6,
                calculator: [10, 50, 100]
            });

            kakao.maps.event.addListener(map, 'click', () => {
                if (currentInfowindow) {
                    currentInfowindow.setMap(null);
                    currentInfowindow = null;
                }
            });
            kakao.maps.event.addListener(map, 'zoom_changed', updateOverlays);
            kakao.maps.event.addListener(map, 'idle', () => {
                if (!isLoadingMarkers) {
                    loadVisibleMarkers(filterStores(allStores, currentPriceRange));
                }
            });
            kakao.maps.event.addListener(clusterer, 'clustered', updateOverlays);

            // 로고 클릭 이벤트 추가
            document.getElementById('logo').addEventListener('click', resetToInitialState);

            initRegionSelect();
            initPriceSelect();
            loadStores(currentRegion, currentPriceRange);

            adjustMapPosition();
            window.addEventListener('resize', adjustMapPosition);
        }

        function updateOverlays() {
            const level = map.getLevel();
            overlays.forEach(overlay => {
                overlay.setMap(level <= 5 ? map : null);
            });
            clickAreas.forEach(area => {
                area.setMap(level <= 5 ? map : null);
            });
            if (currentInfowindow && level > 5) {
                currentInfowindow.setMap(null);
            }
        }

        function clearMap() {
            markers.forEach(marker => marker.setMap(null));
            overlays.forEach(overlay => overlay.setMap(null));
            clickAreas.forEach(area => area.setMap(null));
            clusterer.clear();
            if (currentInfowindow) {
                currentInfowindow.setMap(null);
                currentInfowindow = null;
            }
            markers = [];
            overlays = [];
            clickAreas = [];
        }

        function filterStores(stores, priceRange) {
            if (!priceRange) return stores;
            const priceLimit = parseInt(priceRange.replace('+', ''), 10);
            return stores.filter(store => {
                const price = parseInt(store[1].replace(',', ''), 10) || 0;
                return priceRange === "10000+" ? price >= priceLimit : price <= priceLimit;
            });
        }

        function loadVisibleMarkers(stores) {
            if (isLoadingMarkers) return;
            isLoadingMarkers = true;

            const bounds = map.getBounds();
            const visibleStores = stores.filter(store => 
                store[2] && store[3] && bounds.contain(new kakao.maps.LatLng(store[2], store[3]))
            );

            clearMap();
            loadMarkersInChunks(visibleStores);
        }

        function loadMarkersInChunks(stores, chunkSize = 100) {
            let index = 0;
            function addNextChunk() {
                const chunk = stores.slice(index, index + chunkSize);
                chunk.forEach(store => {
                    const [n, p, lt, lg, c, m, ph, a] = store;
                    const markerPosition = new kakao.maps.LatLng(lt, lg);
                    const marker = new kakao.maps.Marker({
                        position: markerPosition,
                        title: n,
                        clickable: true
                    });
                    markers.push(marker);

                    const cleanName = n.trim().replace(/'/g, "\\'");
                    const overlay = new kakao.maps.CustomOverlay({
                        position: markerPosition,
                        content: `<div class="info-window" onclick="toggleStoreDetails('${cleanName}', '${c || ''}', '${m || ''}', '${p || ''}', '${ph || ''}', '${a || ''}', ${lt}, ${lg})">${cleanName}</div>`,
                        xAnchor: 0.5,
                        yAnchor: 1,
                        zIndex: 10
                    });
                    overlays.push(overlay);

                    const clickArea = new kakao.maps.CustomOverlay({
                        position: markerPosition,
                        content: `<div class="click-area"></div>`,
                        yAnchor: 0.5,
                        xAnchor: 0.5,
                        zIndex: 5
                    });
                    clickAreas.push(clickArea);

                    kakao.maps.event.addListener(marker, 'click', () => toggleStoreDetails(cleanName, c, m, p, ph, a, lt, lg));
                    kakao.maps.event.addListener(clickArea, 'click', () => toggleStoreDetails(cleanName, c, m, p, ph, a, lt, lg));
                });
                clusterer.addMarkers(markers.slice(index, index + chunkSize));
                index += chunkSize;
                if (index < stores.length) {
                    setTimeout(addNextChunk, 50);
                } else {
                    updateOverlays();
                    isLoadingMarkers = false;
                }
            }
            addNextChunk();
        }

        function loadStores(region, priceRange) {
            document.getElementById('loading').style.display = 'block';
            clearMap();
            if (!region) {
                document.getElementById('loading').style.display = 'none';
                return;
            }

            const jsonFile = `stores_by_region/stores_${region}.json.gz`;
            console.log(`Loading file: ${jsonFile}`);
            fetch(jsonFile)
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP 오류: ${response.status}`);
                    return response.arrayBuffer();
                })
                .then(buffer => {
                    const decompressed = pako.inflate(buffer, { to: 'string' });
                    const stores = JSON.parse(decompressed).slice(1);
                    allStores = stores;
                    let filteredStores = filterStores(stores, priceRange);
                    loadVisibleMarkers(filteredStores);
                    if (filteredStores.length > 0) {
                        const bounds = new kakao.maps.LatLngBounds();
                        filteredStores.forEach(store => {
                            if (store[2] && store[3]) bounds.extend(new kakao.maps.LatLng(store[2], store[3]));
                        });
                        map.setBounds(bounds);
                    }
                    document.getElementById('loading').style.display = 'none';
                })
                .catch(error => {
                    console.error(`❌ ${region} 데이터 로드 실패:`, error);
                    document.getElementById('loading').style.display = 'none';
                });
        }

        window.toggleStoreDetails = function(name, category, main_item, price, phone, address, lat, lng) {
            const markerPosition = new kakao.maps.LatLng(lat, lng);
            if (currentInfowindow) {
                currentInfowindow.setMap(null);
                currentInfowindow = null;
            }

            const content = `
                <div class="detail-window" onclick="closeDetailWindow()">
                    <strong>${name}</strong><br>
                    업종: ${category || '정보 없음'}<br>
                    주요 품목: ${main_item || '정보 없음'}<br>
                    가격: ${price ? price + '원' : '정보 없음'}<br>
                    전화번호: ${phone || '정보 없음'}<br>
                    주소: ${address || '정보 없음'}<br>
                </div>
            `;
            const infowindow = new kakao.maps.InfoWindow({
                position: markerPosition,
                content: content,
                zIndex: 20
            });
            infowindow.open(map);
            currentInfowindow = infowindow;
        };

        window.closeDetailWindow = function() {
            if (currentInfowindow) {
                currentInfowindow.setMap(null);
                currentInfowindow = null;
            }
        };

        function initRegionSelect() {
            const select = document.getElementById('region-select');
            select.addEventListener('change', function() {
                currentRegion = this.value;
                loadStores(currentRegion, currentPriceRange);
            });
        }

        function initPriceSelect() {
            const select = document.getElementById('price-select');
            select.addEventListener('change', function() {
                currentPriceRange = this.value;
                if (currentRegion) loadStores(currentRegion, currentPriceRange);
            });
        }

        document.addEventListener('DOMContentLoaded', function() {
            if (typeof kakao === 'undefined') {
                console.error("❌ kakao 객체가 정의되지 않음 - SDK 로드 실패");
                return;
            }
            kakao.maps.load(initMap);
        });
    </script>
</body>
</html>