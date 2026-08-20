# 📚 Lessons from Psyche Network — บทเรียนจากเครือข่าย Psyche

> **What obstacles did the world's first internet-scale decentralized training network face — and how did it solve them? We studied the Psyche Network (Nous Research's decentralized training infrastructure, built on DisTrO) and documented the lessons here, so every developer building the ASEAN Grid starts with proven answers — not guesswork.**
>
> **เครือข่ายเทรนโมเดลแบบกระจายผ่านอินเทอร์เน็ตเครือข่ายแรกของโลกเจออุปสรรคอะไรบ้าง และแก้อย่างไร? เราศึกษา Psyche Network (โครงสร้างพื้นฐานการเทรนแบบกระจายของ Nous Research ที่สร้างบน DisTrO) และบันทึกบทเรียนไว้ที่นี่ เพื่อให้ทุกคนที่มาร่วมสร้าง ASEAN Grid เริ่มต้นด้วยคำตอบที่พิสูจน์แล้ว — ไม่ใช่การเดา**

---

## Why this document exists — ทำไมต้องมีเอกสารนี้

Psyche Network proved that training a large language model (Consilience 40B) across distributed, heterogeneous hardware connected over the internet is possible. But "possible" did not mean "easy" — the network had to be designed around real obstacles. We studied the official Psyche architecture announcement and extracted the four obstacles and their solutions, so our network does not rediscover them the hard way.

Psyche Network พิสูจน์แล้วว่าการเทรนโมเดลขนาดใหญ่ (Consilience 40B) บนฮาร์ดแวร์หลากหลายที่กระจายอยู่ทั่วโลกผ่านอินเทอร์เน็ตเป็นไปได้จริง แต่ "เป็นไปได้" ไม่ได้แปลว่า "ง่าย" — เครือข่ายต้องถูกออกแบบให้อยู่รอดกับอุปสรรคจริง เราศึกษาบทความสถาปัตยกรรม Psyche อย่างเป็นทางการ และสรุปอุปสรรค 4 ข้อพร้อมวิธีแก้ เพื่อให้เครือข่ายของเราไม่ต้องเจอปัญหาแบบเดียวกันโดยไม่รู้ทางแก้

---

## Obstacle 1: Malicious actors — อุปสรรคที่ 1: คนโกง

**The problem / ปัญหา:** An open network lets anyone join — and some participants will submit garbage results or fake work to earn rewards without computing. / เครือข่ายเปิดให้ใครก็ได้เข้าร่วม — และบางคนจะส่งผลขยะหรือผลงานปลอมเพื่อรับรางวัลโดยไม่คำนวณจริง

**Psyche's answer / วิธีแก้ของ Psyche:** Three client roles enforce honesty: *Training* (compute gradients and share), *Witnessing* (verify other clients are alive and correct), and *Verifying* (recompute and compare results to detect malicious actors). / บทบาท 3 ชั้นของ client บังคับความซื่อสัตย์: *Training* (คำนวณ gradient และแบ่งปัน), *Witnessing* (ตรวจว่า client อื่นยังทำงานและถูกต้อง), และ *Verifying* (คำนวณซ้ำและเทียบผลเพื่อตรวจจับผู้ไม่หวังดี)

---

## Obstacle 2: Nodes churn in and out — อุปสรรคที่ 2: เครื่องเข้าออกตลอดเวลา

**The problem / ปัญหา:** Compute providers can stop contributing on short notice — a machine that joins today may leave tomorrow for a better-paying job. / ผู้ให้พลังสามารถหยุดร่วมได้ตลอดเวลา — เครื่องที่เข้ามาวันนี้อาจออกพรุ่งนี้เพื่อไปทำงานที่จ่ายดีกว่า

**Psyche's answer / วิธีแก้ของ Psyche:** Training is divided into *epochs* with natural pause points. New clients download a checkpoint of the model during onboarding; clients can safely off-board between epochs. / การเทรนแบ่งเป็น *epoch* มีจุดพักตามธรรมชาติ Client ใหม่ดาวน์โหลด checkpoint ของโมเดลตอนเข้ามา และออกได้อย่างปลอดภัยระหว่าง epoch

---

## Obstacle 3: Bandwidth is the bottleneck — อุปสรรคที่ 3: แบนด์วิดท์คือคอขวด

**The problem / ปัญหา:** In centralized training, GPUs sit next to each other with ultra-fast interconnects. Over the internet, the data exchanged between nodes can become slower than the computation itself. / ในการเทรนแบบรวมศูนย์ GPU อยู่ติดกันเชื่อมด้วยสายความเร็วสูง แต่ผ่านอินเทอร์เน็ต การแลกเปลี่ยนข้อมูลระหว่างโหนดอาจช้ากว่าการคำนวณเอง

**Psyche's answer / วิธีแก้ของ Psyche:** DisTrO compresses inter-node communication by three to four orders of magnitude, and further reduces bandwidth by "quantizing" the Discrete Cosine Transform of momentums — sending only the *sign* of the transformed data. Communication latency stops being the bottleneck as models scale. / DisTrO บีบอัดการสื่อสารระหว่างโหนดลง 1,000-10,000 เท่า และลดแบนด์วิดท์อีกขั้นด้วยการ "quantize" DCT ของ momentum — ส่งเพียง *เครื่องหมาย* ของข้อมูลที่แปลงแล้ว ทำให้ latency การสื่อสารไม่เป็นคอขวดอีกต่อไปเมื่อโมเดลใหญ่ขึ้น

---

## Obstacle 4: Untrusted, heterogeneous hardware — อุปสรรคที่ 4: ฮาร์ดแวร์หลากหลายที่ไม่น่าเชื่อถือ

**The problem / ปัญหา:** Machines worldwide have different specs, uptime, and security postures — and connections must not be impersonated. / เครื่องทั่วโลกมีสเปก อัตราการออนไลน์ และความปลอดภัยต่างกัน — และการเชื่อมต่อต้องไม่ถูกปลอมแปลง

**Psyche's answer / วิธีแก้ของ Psyche:** Every peer connection is end-to-end encrypted and authenticated by default: NodeIds are cryptographic keys, verified during the handshake, over QUIC. / ทุกการเชื่อมต่อ peer เข้ารหัสและพิสูจน์ตัวตนแบบ end-to-end โดยค่าเริ่มต้น: NodeId เป็นคีย์เข้ารหัส ตรวจสอบระหว่าง handshake ผ่าน QUIC

---

## The takeaway — บทสรุป

> **Every obstacle the Psyche Network faced is an obstacle any distributed network will face. Every answer they designed is an answer others can adopt. They proved the path exists.**
>
> **ทุกอุปสรรคที่ Psyche เจอ คืออุปสรรคที่เครือข่ายกระจายทุกระบบจะเจอ ทุกคำตอบที่เขาออกแบบ คือคำตอบที่ผู้อื่นนำมาใช้ได้ เขาพิสูจน์ว่าเส้นทางมีอยู่จริง**

---

*Sources: The Psyche Network Architecture (Nous Research, May 2025) — nousresearch.com/nous-psyche. DisTrO repository — github.com/NousResearch/DisTrO. Licensed under AGPL-3.0.*
*แหล่งอ้างอิง: บทความสถาปัตยกรรม Psyche Network (Nous Research, พ.ค. 2025) — nousresearch.com/nous-psyche และ DisTrO repository — github.com/NousResearch/DisTrO*
