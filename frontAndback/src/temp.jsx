import React, { useState, useEffect } from 'react';

function App() {
  const [ads, setAds] = useState([]);

  useEffect(() => {
    fetch('/api/ads')
      .then((res) => res.json())
      .then((data) => {
        // ✅ 경로에서 불필요한 따옴표 제거
        const cleanedData = data.map(ad => ({
          ...ad,
          image_path: ad.image_path.replace(/^"|"$/g, "")  // 🔥 앞뒤의 " 제거
        }));
        console.log("받은 데이터:", cleanedData);
        setAds(cleanedData);
      })
      .catch((error) => {
        console.error('Error fetching ads:', error);
      });
  }, []);

  return (
    <>
      <h1>📢 광고 목록</h1>
      <ul>
        {ads.map((ad, idx) => (
          <li key={idx}>
            <strong>{ad.title}</strong><br />
            광고 ID: {ad.ad_id}<br />
            이미지 경로: {ad.image_path}<br />
            <img src={`/${ad.image_path}`} alt={ad.title} width="200" />
            <hr />
          </li>
        ))}
      </ul>
    </>
  );
}

export default App;
