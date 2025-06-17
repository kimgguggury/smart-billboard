// export default App;
import React, { useEffect, useState } from "react";
import axios from "axios";
import './App.css';

function App() {
  const [analyzeResult, setAnalyzeResult] = useState([]);
  const [ads, setAds] = useState([]);
  const [selectedAd, setSelectedAd] = useState(null);
  // const safeImagePath = selectedAd.image_path.replace(/\\/g, '/');

  //   useEffect(() => {
  //   if (selectedAd && analyzeResult.length > 0) {
  //     console.log("👁️‍🗨️ 광고 시청 기록 전송 - ad_id:", selectedAd.ad_id);
      
  //     axios.post("http://localhost:5000/api/viewed", {
  //       ad_id: selectedAd.ad_id,
  //       people: analyzeResult
  //     })
  //     .then((res) => {
  //       console.log("✅ view_count 증가 완료:", res.data);
  //     })
  //     .catch((error) => {
  //       console.error("❌ view_count 업데이트 실패:", error);
  //     });
  //   }
  // }, [selectedAd]);
  useEffect(() => {
    const fetchAds = async () => {
      try {
        const response = await axios.get("http://localhost:5000/api/ads");
        setAds(response.data);
      } catch (error) {
        console.error("Error fetching ads:", error);
      }
    };

    fetchAds();
    

    // ✅ SSE: 실시간 분석 결과 수신
    const eventSource = new EventSource("http://localhost:5000/api/analyze-stream");
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received Analysis Data:", data);
      
      if (Array.isArray(data) && data.length > 0) {
        setAnalyzeResult(data);
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
  if (analyzeResult.length > 0) {
    const ageGenderCount = Array.from(Array(2), () => Array(7).fill(0));

    analyzeResult.forEach((person) => {
      const ageGroup = Math.min(Math.floor(person.age / 10), 6);
      const genderIndex = person.gender === "Man" ? 0 : 1;
      ageGenderCount[genderIndex][ageGroup] += 1;
    });

    console.log("Age-Gender Count Matrix:", ageGenderCount);

    // 최댓값 후보들을 수집
    let maxCount = 0;
    let candidates = [];

    for (let gender = 0; gender < 2; gender++) {
      for (let ageGroup = 0; ageGroup < 7; ageGroup++) {
        const count = ageGenderCount[gender][ageGroup];
        if (count > maxCount) {
          maxCount = count;
          candidates = [{ gender, ageGroup }];
        } else if (count === maxCount && count > 0) {
          candidates.push({ gender, ageGroup });
        }
      }
    }

    // 후보 중 랜덤으로 하나 선택
    if (candidates.length > 0) {
      const randomTarget = candidates[Math.floor(Math.random() * candidates.length)];
      const genderStr = randomTarget.gender === 0 ? "M" : "W";
      const targetAge = randomTarget.ageGroup.toString();

      console.log("🎯 최종 선택된 타겟:", genderStr, targetAge);

      const filteredAds = ads.filter(
        (ad) =>
          ad.target_sex === genderStr &&
          ad.target_age.toString() === targetAge
      );

      console.log("Filtered Ads:", filteredAds);

      if (filteredAds.length > 0) {
        const randomIndex = Math.floor(Math.random() * filteredAds.length);
        const chosenAd = filteredAds[randomIndex];
        setSelectedAd(chosenAd);

        axios.post("http://localhost:5000/api/current-ad", {
          ad_id: chosenAd.ad_id,
        }).catch((error) => {
          console.error("current_ad.json 저장 실패:", error);
        });
      } else {
        setSelectedAd(null);
      }
    } else {
      setSelectedAd(null);
    }
  }
}, [analyzeResult, ads]);


  return (
    <div className="container">
      {selectedAd ? (
        <div className="content">
          <h2>{selectedAd.title}</h2>
         <img
            src={`http://localhost:5000/static/${selectedAd.image_path.replace(/\\/g, '/')}`}
            alt={selectedAd.title}
          />

        </div>
      ) : (
        <p>No matching ad found.</p>
      )}
    </div>
  );
}

export default App;
