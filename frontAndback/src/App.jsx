// export default App;
import React, { useEffect, useState } from "react";
import axios from "axios";
import './App.css';

function App() {
  const [analyzeResult, setAnalyzeResult] = useState([]);
  const [ads, setAds] = useState([]);
  const [selectedAd, setSelectedAd] = useState(null);
  // const safeImagePath = selectedAd.image_path.replace(/\\/g, '/');
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

      let maxCount = 0;
      let targetGender = 0;
      let targetAgeGroup = 0;

      for (let gender = 0; gender < 2; gender++) {
        for (let ageGroup = 0; ageGroup < 7; ageGroup++) {
          if (ageGenderCount[gender][ageGroup] > maxCount) {
            maxCount = ageGenderCount[gender][ageGroup];
            targetGender = gender;
            targetAgeGroup = ageGroup;
          }
        }
      }

      const genderStr = targetGender === 0 ? "M" : "W";
      const targetAge = targetAgeGroup.toString();
      console.log("Selected Target:", genderStr, targetAge);

      const filteredAds = ads.filter(
        (ad) =>
          ad.target_sex === genderStr &&
          ad.target_age.toString() === targetAge
      );
      console.log("Filtered Ads:", filteredAds);

      if (filteredAds.length > 0) {
        setSelectedAd(filteredAds[0]);

        axios.post("http://localhost:5000/api/current-ad", {
          ad_id: filteredAds[0].ad_id,
        }).catch((error) => {
          console.error("current_ad.json 저장 실패:", error);
        });

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
