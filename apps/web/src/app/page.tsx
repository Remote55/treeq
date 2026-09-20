'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { EditorialSection } from '../components/editorial/editorial-section';
import { TechnicalDetail } from '../components/editorial/technical-detail';
import { EvidenceMetric } from '../components/evidence/evidence-metric';
import { AppHeader } from '../components/layout/app-header';
import { ScrollToTop } from '../components/layout/scroll-to-top';
import { Button } from '../components/ui/button';
import { CORE_DEMO_EVIDENCE } from '../generated/core-demo-evidence';
import { DatasetGallery } from '@/components/Dataset/dataset-gallery';
import { PointCloudViewer } from '@/components/viewer/point-cloud-viewer';
import { type PointCloud } from '@/lib/demo-pointcloud';
import { decimate, parsePly } from '@/lib/ply-loader';
import { LIMITS_LABEL_TH } from '@/lib/upload-limits';

const { baseline, candidate } = CORE_DEMO_EVIDENCE;
const { demol65, cameroon61, pointnetIndependent } = CORE_DEMO_EVIDENCE.validation;
// The separation quality that describes what ships: the default backend,
// measured on a cohort it never trained on. The Wan held-out numbers belong to
// the candidate and to a split that also picked its best epoch.
const baselineExternalWoodIoU = pointnetIndependent.baseline.externalMacroWoodIoU;
const candidateExternalWoodIoU = pointnetIndependent.candidate.externalMacroWoodIoU;

const MAX_HERO_POINTS = 200_000;

const JOURNEY = [
  {
    step: '01',
    title: 'รับภาพสามมิติของต้นไม้',
    description:
      'รองรับข้อมูล Point Cloud จากเครื่องสแกน LiDAR ภาคพื้นดิน (TLS)',
    technical: [
      'Point Cloud รูปแบบ .ply',
      LIMITS_LABEL_TH,
    ],
  },
  {
    step: '02',
    title: 'แยกลำต้นออกจากใบไม้',
    description:
      'คัดแยกจุดที่เป็นลำต้นออกจากใบไม้ด้วยอัลกอริทึมเชิงเรขาคณิต เพื่อลดความคลาดเคลื่อนในการคำนวณชีวมวล',
    technical: [
      `${baseline.backend} เป็นตัวที่ใช้จริง`,
      `${candidate.displayName} ยังเป็น ${candidate.status} ไม่ได้ถูกนำมาใช้`,
      // IoU, not accuracy — and the number has to be the one that describes
      // what runs. 0.418 is the candidate's, on a split that also selected its
      // best epoch; tlsep, the backend named on the line above, scores this.
      `ความซ้อนทับกับเฉลย (IoU) ของลำต้น ${baselineExternalWoodIoU.toFixed(3)} บนชุดข้อมูลนอก`,
    ],
  },
  {
    step: '03',
    title: 'วัดขนาดต้นไม้',
    description:
      'ประเมินขนาดลำต้นและความสูงรวม และสร้างแบบจำลองทรงกระบอก เพื่อคำนวณปริมาตรเนื้อไม้',
    technical: [
      'วัดเส้นผ่านศูนย์กลางลำต้นที่ระดับ 1.3 เมตร',
      'คำนวณปริมาตรจากแบบจำลองทรงกระบอก QSM',
      `ค่าคลาดเคลื่อนเฉลี่ย ${demol65.dbhMaeCm.toFixed(2)} ซม. จากต้นไม้เขตอบอุ่น 65 ต้น`,
      // The tropical figure belongs beside the temperate one, not instead of
      // it: the cohorts answer different questions and both are quoted.
      `${cameroon61.dbhGateAppliedMaeCm.toFixed(2)} ซม. จากต้นไม้เขตร้อนที่โค่นและชั่งจริง ` +
        `(${cameroon61.gatePassedTrees} ต้นที่ผ่านเกณฑ์คุณภาพการวัด)`,
    ],
  },
  {
    step: '04',
    title: 'คำนวณคาร์บอน',
    description:
      'คำนวณปริมาณชีวมวล คาร์บอนสะสม และ CO₂e ตามสมการแอลโลเมตริก พร้อมบันทึกแหล่งที่มาของข้อมูล',
    technical: [
      'ใช้สมการ Chave 2014',
      'ชีวมวลใต้ดิน = ชีวมวลเหนือดิน × 0.24',
      'คาร์บอน = ชีวมวล × 0.47',
      'CO₂e = คาร์บอน × 44/12 ตามแนวทาง IPCC 2006',
      'CO₂e คือปริมาณก๊าซเรือนกระจกเทียบเท่าคาร์บอนไดออกไซด์',
    ],
  },
] as const;

const PROJECT_OBJECTIVES = [
  {
    step: '01',
    title: 'ลดอุปสรรคทางภูมิศาสตร์',
    summary:
      'ลดความจำเป็นในการเดินเท้าสำรวจพื้นที่ลาดชัน พื้นที่ห่างไกล หรือพื้นที่ที่เข้าถึงได้ยาก',
    detail:
      'ช่วยให้กลุ่มเกษตรกรสามารถเก็บข้อมูลพื้นที่ป่าของตนได้สะดวกขึ้น และผู้ตรวจสอบสามารถประเมินโครงสร้างป่าในเบื้องต้นจากระยะไกล',
    tone: 'bg-deep-forest',
  },
  {
    step: '02',
    title: 'ลดต้นทุนและเวลา',
    summary:
      'เปลี่ยนการวัดต้นไม้ทีละต้นด้วยแรงงานคน ให้เป็นการประมวลผลข้อมูล Point Cloud แบบอัตโนมัติ',
    detail:
      'ช่วยให้เกษตรกรและชุมชนประเมินศักยภาพคาร์บอนเบื้องต้นด้วยต้นทุนที่ต่ำลง ลดระยะเวลาการสำรวจ และลดความเสี่ยงก่อนว่าจ้างผู้ตรวจสอบจริง',
    tone: 'bg-moss',
  },
  {
    step: '03',
    title: 'ยกระดับความโปร่งใส',
    summary:
      'แสดงแหล่งที่มาของข้อมูล ขั้นตอนการประมวลผล และวิธีการคำนวณอย่างเป็นระบบ',
    detail:
      'ช่วยเพิ่มความมั่นใจให้แก่ผู้ตรวจสอบ และเพิ่มโอกาสให้พื้นที่ป่าห่างไกลเข้าสู่กระบวนการประเมินและรับรองด้านคาร์บอน',
    tone: 'bg-evidence-amber',
  },
] as const;

export default function HomePage() {
  const [heroCloud, setHeroCloud] = useState<PointCloud | null>(null);
  const [heroCloudError, setHeroCloudError] = useState<string | null>(
    null,
  );
  const [isHeroCloudLoading, setIsHeroCloudLoading] = useState(true);

useEffect(() => {
  let cancelled = false;

  async function loadHeroCloud() {
    try {
      setIsHeroCloudLoading(true);
      setHeroCloudError(null);

      const response = await fetch('/demo/scholar-tree-viewer.ply');

      if (!response.ok) {
        throw new Error(
          `ไม่พบไฟล์ Point Cloud (HTTP ${response.status})`,
        );
      }

      const buffer = await response.arrayBuffer();

      const parsedCloud = decimate(
        parsePly(buffer),
        MAX_HERO_POINTS,
      );

      if (
        parsedCloud.positions.length === 0 ||
        parsedCloud.classes.length === 0
      ) {
        throw new Error(
          'ไฟล์นี้ไม่มีข้อมูลจุดที่ระบบสามารถอ่านได้',
        );
      }

      if (!cancelled) {
        setHeroCloud(parsedCloud);
      }
    } catch (error) {
      if (!cancelled) {
        setHeroCloud(null);
        setHeroCloudError(
          error instanceof Error
            ? error.message
            : 'ไม่สามารถโหลดไฟล์ Point Cloud ได้',
        );
      }
    } finally {
      if (!cancelled) {
        setIsHeroCloudLoading(false);
      }
    }
  }

  void loadHeroCloud();

  return () => {
    cancelled = true;
  };
}, []);



  return (
    <div className="min-h-screen overflow-x-hidden bg-gallery-ivory text-forest-ink">
     <a
  href="#main-content"
  className="sr-only rounded-full bg-canopy px-5 py-3 text-sm font-medium text-paper focus:not-sr-only focus:fixed focus:left-5 focus:top-4 focus:z-[60]"
>
  ข้ามไปยังเนื้อหาหลัก
</a>

     <AppHeader />

<div className="h-16" aria-hidden="true" />

<main id="main-content">
        <section className="mx-auto max-w-7xl px-5 pb-12 pt-8 sm:px-8">
          <div className="grid grid-cols-1 items-stretch gap-10 lg:min-h-[35.625rem] lg:grid-cols-12">
            <div className="flex flex-col justify-center py-4 lg:col-span-6 lg:pr-10">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-moss/20 bg-moss/5 px-3 py-1.5">
                <span className="h-2 w-2 rounded-full bg-moss" />

                <span className="text-xs font-semibold tracking-wide text-canopy">
                  TREEQ CARBON / ตรวจสอบย้อนกลับได้ทุกตัวเลข
                </span>
              </div>

              <h1 className="mt-7 max-w-[14ch] text-balance font-display text-[2.75rem] font-medium leading-[1.12] tracking-[-0.035em] text-forest-ink sm:text-5xl lg:text-[3.6rem]">
                วิเคราะห์คาร์บอนจาก Point Cloud ผ่านขนาดลำต้นที่ตรวจสอบได้
              </h1>

              <p className="mt-6 max-w-xl text-base leading-8 text-canopy sm:text-lg">
                วัดขนาดลำต้นและโครงสร้างต้นไม้จาก Point Cloud
                แล้วประเมินปริมาณคาร์บอนสะสม พร้อมหลักฐานที่ตรวจสอบย้อนกลับได้ทุกตัวเลข
              </p>

              {/* The upload page runs the 3D separation in the browser, but the
                  carbon step needs the pipeline on a backend and there is no
                  public deployment. Saying "upload to get carbon" here would be
                  a claim the site cannot honour — the same defect the evidence
                  gates catch in numbers, arriving instead as copy. */}
              <p className="mt-3 max-w-xl text-sm leading-7 text-canopy/80">
                เวอร์ชันออนไลน์นี้แยกลำต้น / ใบ / พื้นดิน ให้ดูในเบราว์เซอร์
                ส่วนการคำนวณคาร์บอนต้องรัน pipeline บน backend ซึ่งยังไม่มี deployment สาธารณะ —
                ผลที่ตรวจสอบแล้วดูได้ที่หน้าสาธิต
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <Button
                  render={<Link href="/dashboard/viewer" />}
                  variant="editorial"
                  size="xl"
                  className="justify-center sm:min-w-48"
                >
                  อัปโหลดดูการแยก 3 มิติ
                </Button>

                {/* /demo is the hash-verified evidence page: the reconciled
                    tree counts, the per-tree exclusion reasons, and the
                    PointNet++ verdict. The nav became a single-page scroll and
                    took its menu entry with it, leaving the page reachable only
                    by typing the URL, so this button is now the way in. */}
                <Button
                  render={<Link href="/demo" />}
                  variant="editorialOutline"
                  size="xl"
                  className="justify-center sm:min-w-36"
                >
                  ดูผลการประเมิน
                </Button>
              </div>

              
            </div>

            <div className="relative mt-6 min-h-[30rem] overflow-hidden rounded-[2rem] bg-forest-ink shadow-[0_32px_80px_-24px_rgba(14,42,29,0.45)] sm:mt-8 lg:col-span-6 lg:mt-10 lg:min-h-[35.625rem]">
              {heroCloud ? (
                <>
                  <PointCloudViewer
                    positions={heroCloud.positions}
                    classes={heroCloud.classes}
                    labelled={heroCloud.labelled}
                    className="absolute inset-0 h-full w-full"
                  />

                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-deep-forest/55 via-transparent to-deep-forest/80" />

                  <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-4 p-5 sm:p-6">
                    <div className="min-w-0">
                      <div className="inline-flex items-center gap-2 rounded-full border border-paper/15 bg-deep-forest/75 px-3 py-1.5 backdrop-blur-md">
                        <span className="h-2 w-2 rounded-full bg-lichen" />

                        <span className="text-xs font-medium text-paper">
                          Point Cloud จากไฟล์จริง
                        </span>
                      </div>

                     

                    </div>

                    <div className="rounded-full border border-paper/15 bg-deep-forest/75 px-3 py-2 text-xs font-medium text-paper backdrop-blur-md">
                      {heroCloud.classes.length.toLocaleString()} จุด
                    </div>
                  </div>

                  <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col gap-3 p-5 sm:flex-row sm:items-end sm:justify-between sm:p-6">
                    

                    <div className="rounded-full border border-paper/15 bg-deep-forest/70 px-4 py-2 text-[11px] text-mist backdrop-blur-md">
                      ลากเพื่อหมุน · เลื่อนเมาส์เพื่อซูม
                    </div>
                    
                  </div>
                </>
              ) : (
                <div className="flex min-h-[30rem] items-center justify-center px-6 text-center lg:min-h-[35.625rem]">
                  {isHeroCloudLoading ? (
                    <div>
                      <div className="relative mx-auto h-12 w-12">
                        <div className="absolute inset-0 rounded-full border-4 border-lichen/20" />
                        <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-lichen" />
                      </div>

                      <p className="mt-5 font-display text-lg font-medium text-paper">
                        กำลังโหลด Point Cloud
                      </p>

                      <p className="mt-2 text-sm text-mist">
                        กำลังเตรียมข้อมูลสามมิติสำหรับแสดงผล
                      </p>
                    </div>
                  ) : (
                    <div className="max-w-sm">
                      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-ember/15 text-xl text-ember">
                        !
                      </div>

                      <p className="mt-5 font-display text-xl font-medium text-paper">
                        โหลด Point Cloud ไม่สำเร็จ
                      </p>

                      <p className="mt-2 text-sm leading-7 text-mist">
                        {heroCloudError}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </section>

<div
  id="problem"
  className="scroll-mt-20"
  data-editorial-beat="problem"
>          <EditorialSection
            className="border-t border-hairline bg-paper"
            title="ข้อจำกัดของการสำรวจแบบเดิม"
            description="วิธีการสำรวจแบบดั้งเดิมไม่สามารถรองรับผืนป่าขนาดใหญ่หรือภูมิประเทศที่เป็นภูเขาได้ การส่งคนเข้าไปเดินวัดขนาดลำต้นทีละต้นในพื้นที่ลาดชันหรือห่างไกล เป็นอุปสรรคสำคัญที่ทำให้หลายพื้นที่ไม่สามารถเข้าถึงการประเมินคาร์บอนได้"
          >
            <div className="grid gap-5 md:grid-cols-3">
              <div className="rounded-2xl border border-hairline bg-gallery-ivory p-6">
                <h3 className="font-display text-xl font-medium text-forest-ink">
                  เข้าถึงพื้นที่ได้ยาก
                </h3>

                <p className="mt-3 text-sm leading-7 text-canopy">
                  พื้นที่ลาดชัน พื้นที่ภูเขา และพื้นที่ห่างไกล
                  ทำให้การเดินสำรวจมีความเสี่ยงและใช้เวลาสูง
                </p>
              </div>

              <div className="rounded-2xl border border-hairline bg-gallery-ivory p-6">
                <h3 className="font-display text-xl font-medium text-forest-ink">
                  ใช้แรงงานจำนวนมาก
                </h3>

                <p className="mt-3 text-sm leading-7 text-canopy">
                  เจ้าหน้าที่ต้องเดินวัดขนาดต้นไม้ทีละต้น
                  ทำให้ไม่เหมาะกับพื้นที่ขนาดใหญ่
                </p>
              </div>

              <div className="rounded-2xl border border-hairline bg-gallery-ivory p-6">
                <h3 className="font-display text-xl font-medium text-forest-ink">
                  ตรวจสอบย้อนหลังได้ยาก
                </h3>

                <p className="mt-3 text-sm leading-7 text-canopy">
                  ผลลัพธ์จากการสำรวจอาจขาดหลักฐานดิจิทัล
                  ที่เชื่อมโยงกลับไปยังข้อมูลต้นทาง
                </p>
              </div>
            </div>
          </EditorialSection>
        </div>

        <div id="objectives" data-editorial-beat="objectives">
          <EditorialSection
            className="border-t border-hairline bg-gallery-ivory"
            title="เป้าหมายของโครงการ"
            description="TreeQ Carbon Platform พัฒนาขึ้นเพื่อช่วยลดข้อจำกัดของการสำรวจป่าแบบเดิม ด้วยการประยุกต์ใช้ข้อมูล Point Cloud และระบบประมวลผลอัตโนมัติ"
          >
            <div className="grid items-stretch gap-6 lg:grid-cols-3">
              {PROJECT_OBJECTIVES.map((objective) => (
                <article
                  key={objective.step}
                  className="flex h-full flex-col rounded-2xl border border-hairline bg-paper p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg sm:p-7"
                >
                  <div className="flex items-center gap-4">
                    <span
                      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full font-display text-lg font-semibold text-paper ${objective.tone}`}
                    >
                      {objective.step}
                    </span>

                    <h3 className="font-display text-xl font-semibold leading-snug text-forest-ink sm:text-2xl">
                      {objective.title}
                    </h3>
                  </div>

                  <p className="mt-5 text-base leading-8 text-canopy">
                    {objective.summary}
                  </p>

                  <div className="mt-6 flex-1 rounded-xl bg-gallery-ivory p-5">
                    <p className="text-sm leading-7 text-canopy">
                      {objective.detail}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </EditorialSection>
        </div>

        <div id="how" data-editorial-beat="journey">
          <EditorialSection
            className="bg-paper"
            title="วิธีทำงาน"
            description="ระบบแปลงข้อมูล Point Cloud สู่ตัวเลขคาร์บอนสะสมผ่าน 4 ขั้นตอนหลัก โดยระบุเทคนิคและสมการที่ใช้อย่างชัดเจน"
          >
            <div className="relative border-y border-hairline py-4">
              <div className="absolute bottom-0 left-[6.5rem] top-0 hidden w-px bg-hairline sm:block" />

              <ol className="relative z-10">
                {JOURNEY.map((item) => (
                  <li
                    key={item.step}
                    className="group grid gap-4 border-b border-hairline py-8 last:border-b-0 sm:grid-cols-[5rem_minmax(0,1fr)_minmax(0,1.2fr)] sm:gap-8 sm:border-b-0 sm:pb-12"
                  >
                    <div className="flex items-start">
                      <span className="flex h-10 w-10 items-center justify-center rounded-full border border-evidence-amber bg-paper font-mono text-sm font-medium text-evidence-amber shadow-sm transition-colors group-hover:bg-evidence-amber group-hover:text-paper">
                        {item.step}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-display text-2xl font-medium text-forest-ink">
                        {item.title}
                      </h3>

                      <p className="mt-3 text-base leading-relaxed text-canopy">
                        {item.description}
                      </p>
                    </div>

                    <div className="rounded-xl border border-hairline/50 bg-gallery-ivory p-5 shadow-sm">
                      <TechnicalDetail>
                        <ul className="space-y-2">
                          {item.technical.map((line) => (
                            <li
                              key={line}
                              className="flex items-start gap-2 text-sm text-forest-ink/80"
                            >
                              <span className="mt-1.5 block h-1.5 w-1.5 shrink-0 rounded-full bg-evidence-amber/60" />
                              <span>{line}</span>
                            </li>
                          ))}
                        </ul>
                      </TechnicalDetail>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </EditorialSection>
        </div>

<div
  id="tech"
  className="scroll-mt-20"
  data-editorial-beat="three-dimensional-evidence"
>
  <EditorialSection
    className="border-y border-hairline bg-paper"
    title="ชุดข้อมูล (Dataset) ที่ใช้"
    description="ตัวอย่างชุดข้อมูลต้นไม้สามมิติที่แสดงลำดับตั้งแต่ข้อมูล Point Cloud ต้นฉบับ ผลการซ้อนทับสำหรับตรวจสอบโครงสร้าง จนถึงแบบจำลองสามมิติที่ได้หลังการประมวลผล"
  >
    <DatasetGallery />

    <div className="mt-5 rounded-xl border border-hairline bg-gallery-ivory px-5 py-4 sm:flex sm:items-start sm:justify-between sm:gap-6">
      <div>
        <p className="editorial-eyebrow-th text-canopy">
          แหล่งที่มาของชุดข้อมูล
        </p>

        <p className="mt-2 text-sm font-medium leading-6 text-forest-ink">
          QSMs, point cloud and harvest data from a destructive forest
          biomass experiment in Belgium using terrestrial laser scanning
        </p>

        <p className="mt-1 text-xs leading-6 text-canopy">
          Demol, Miro · Gielen, Bert · Verbeeck, Hans (2021)
        </p>

        <p className="mt-1 text-xs leading-6 text-canopy">
          DOI: 10.5281/zenodo.4557401
        </p>
      </div>

      <a
        href="https://zenodo.org/records/4557401"
        target="_blank"
        rel="noopener noreferrer"
        className="focus-ring mt-4 inline-flex shrink-0 items-center justify-center rounded-full border border-moss/40 bg-paper px-4 py-2.5 text-sm font-medium text-canopy transition-colors hover:border-moss hover:bg-moss/10 hover:text-deep-forest sm:mt-0"
      >
        ดูชุดข้อมูลต้นฉบับ
        
      </a>
    </div>
  </EditorialSection>
</div>

<div
  id="proof"
  className="scroll-mt-20"
  data-editorial-beat="validation"
>
  <EditorialSection
    className="bg-gallery-ivory"
    title="ความแม่นยำ"
    description="ผลการประเมินอ้างอิงจากชุดข้อมูลทดสอบ โดยเปิดเผยข้อจำกัดของระบบอย่างตรงไปตรงมา"
  >
    <div className="grid items-stretch gap-4 md:grid-cols-3">
      {/* 0.418 belonged to the trained candidate on the Wan held-out split -
          and PROJECT_SPEC.md:15 records that the same split chose the best
          epoch, so it is selection-contaminated. Shown here it read as the
          quality of the separation that ships. It is not: tlsep, the default
          this site names as the one in use, scores 0.196 macro wood IoU on a
          cohort it never saw (result.json /baseline/external_segmentation).
          The honest figure is the lower one, on the harder set. */}
      <div className="h-full [&>*]:h-full">
        <EvidenceMetric
          label="ค่า IoU การแยกลำต้น"
          value={baselineExternalWoodIoU.toFixed(3)}
          note={`สัดส่วนความซ้อนทับกับเฉลย (0–1) ไม่ใช่เปอร์เซ็นต์ความถูกต้อง · วิธีที่ใช้จริง (${baseline.backend}) บนชุดข้อมูลนอกที่ไม่เคยเห็น`}
          tone="dark"
        />
      </div>

      <div className="h-full [&>*]:h-full">
        <EvidenceMetric
          label="วิธีที่ใช้จริง"
          value={baseline.backend}
          note={`${candidate.displayName} ทำได้ ${candidateExternalWoodIoU.toFixed(3)} บนชุดเดียวกัน แต่วัดขนาดได้แย่กว่า จึงไม่ถูกนำมาใช้`}
          tone="lichen"
        />
      </div>

      {/* Two cohorts, because they answer different questions and the
          tropical one is the question this product is for. The panel used to
          carry only the Belgian figure, which is a true number about
          temperate isolated trees presented as the accuracy of a platform
          aimed at tropical forest. */}
      <div className="h-full [&>*]:h-full">
        <EvidenceMetric
          label="ค่าคลาดเคลื่อนการวัดขนาดลำต้น · เขตอบอุ่น"
          value={`${demol65.dbhMaeCm.toFixed(2)} ซม.`}
          note="ทดสอบการวัดเส้นผ่านศูนย์กลางลำต้นกับต้นไม้จริงแยกเดี่ยวจำนวน 65 ต้น (เบลเยียม)"
        />
      </div>
    </div>

    <div className="mt-4 grid items-stretch gap-4 md:grid-cols-3">
      <div className="h-full [&>*]:h-full">
        <EvidenceMetric
          label="ค่าคลาดเคลื่อนการวัดขนาดลำต้น · เขตร้อน"
          value={`${cameroon61.dbhGateAppliedMaeCm.toFixed(2)} ซม.`}
          note={
            `ชุดแคเมอรูนที่โค่นและชั่งจริงทั้งหมด ${cameroon61.trees} ต้น ` +
            `วัดได้ ${cameroon61.treesMeasured} ต้น — ค่านี้มาจาก ${cameroon61.gatePassedTrees} ต้นที่ผ่านเกณฑ์คุณภาพการวัด`
          }
          tone="dark"
        />
      </div>

      {/* The refusal count is not a caveat, it is half the headline. An
          average over the trees that passed says nothing about the trees
          that did not, and 27 of 60 reads as 60 of 60 without this. */}
      <div className="h-full [&>*]:h-full">
        <EvidenceMetric
          label="ต้นที่ระบบปฏิเสธไม่วัด"
          value={`${cameroon61.gateRefusedTrees} จาก ${cameroon61.treesMeasured}`}
          note="ต้นที่ไม่ผ่านเกณฑ์การวัดในชุดนี้ ข้อมูลอ้างอิงไม่มีป้ายกำกับพูพอนรายต้น จึงยังระบุสาเหตุว่าเป็นพูพอนไม่ได้"
          tone="lichen"
        />
      </div>

      <div className="h-full [&>*]:h-full">
        <EvidenceMetric
          label="ค่าคลาดเคลื่อนถ้าบังคับให้ตอบทุกต้น"
          value={`${cameroon61.dbhMaeCm.toFixed(2)} ซม.`}
          note={`ค่าเฉลี่ยความผิดพลาดสัมบูรณ์ของ ${cameroon61.treesMeasured} ต้นที่วัดได้เมื่อไม่ใช้เกณฑ์ปฏิเสธ ไม่ใช่ขอบบนของความผิดพลาดรายต้น`}
        />
      </div>
    </div>
  </EditorialSection>
</div>



       
      </main>

      <footer className="border-t border-hairline bg-paper py-8">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-5 text-sm text-canopy sm:flex-row sm:px-8">
          <span className="font-display text-base text-forest-ink">
            TreeQ Carbon Platform
          </span>

          <span>Prototype · ผลลัพธ์เป็นค่าประมาณ ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง</span>
        </div>
      </footer>

      <ScrollToTop />
    </div>
  );
}
