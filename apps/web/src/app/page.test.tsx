import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { CORE_DEMO_EVIDENCE } from '../generated/core-demo-evidence';
import HomePage from './page';

function getAnchorHrefByLabel(markup: string, label: string) {
  const anchor = (markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? []).find((tag) =>
    tag.includes(`>${label}</a>`),
  );

  return anchor?.match(/\bhref="([^"]+)"/)?.[1];
}

describe('Landing evidence contract', () => {
  it('sends each landing action to the correct route', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(getAnchorHrefByLabel(markup, 'ดูผลการประเมิน')).toBe('/demo');

    // Label changed from 'ทดลองอัปโหลดไฟล์' when the API URL was removed from
    // production. Uploading still works and still runs the separation in the
    // browser; what it no longer does is produce a carbon figure, and the old
    // label promised the whole flow.
    expect(getAnchorHrefByLabel(markup, 'อัปโหลดดูการแยก 3 มิติ')).toBe(
      '/dashboard/viewer',
    );

    // The ดูแผนที่ action is gone with the map route, which the supervisor
    // asked to be taken down until it is finished. Nothing on the landing page
    // may point at it while it does not exist.
    expect(markup).not.toContain('/dashboard/map');
  });

  it('never points an upload promise at the read-only demo route', () => {
    const markup = renderToStaticMarkup(<HomePage />);
    const anchors = markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? [];

    const uploadAnchors = anchors.filter((anchor) =>
      anchor.includes('อัปโหลด'),
    );

    expect(uploadAnchors.length).toBeGreaterThan(0);

    for (const anchor of uploadAnchors) {
      const href = anchor.match(/\bhref="([^"]+)"/)?.[1];

      expect(href).toBeDefined();
      expect(href).not.toBe('/demo');
    }
  });

  it('reports the current validation values and implementation status honestly', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    // The separation figure must be IoU, named as IoU, and must be the number
    // that describes what actually runs. 0.418 is the trained candidate's, on
    // the Wan held-out split that also selected its best epoch; tlsep — the
    // backend this page names as the one in use — scores 0.196 on a cohort it
    // never saw. Quoting the candidate's contaminated number as the system's
    // quality is the failure this guards.
    expect(markup).toContain('0.196');
    expect(markup).toContain('IoU');
    expect(markup).not.toContain('ความแม่นยำการแยก');
    expect(markup).not.toContain('0.418');

    // A tree-diameter error quoted to eleven significant figures claims
    // precision to picometres. Two decimals is what the measurement supports.
    //
    // Asserted against the generated evidence rather than a literal. This read
    // `toContain('1.17')`, which was a fourth copy of a figure that turned out
    // never to have been derived — see docs/ml/DEMOL_EVIDENCE_CHAIN.md. When the
    // real number was worked out, this test failed for quoting the old one,
    // which is the wrong reason for a rounding test to fail.
    const dbhMaeCm = CORE_DEMO_EVIDENCE.validation.demol65.dbhMaeCm;

    expect(markup).toContain(dbhMaeCm.toFixed(2));
    expect(markup).toContain('ซม.');
    expect(markup).not.toContain(String(dbhMaeCm));

    expect(markup).toContain('ค่าคลาดเคลื่อนการวัดขนาดลำต้น');

    expect(markup).toContain('tlsep');
    expect(markup).toContain('PointNet++');
    expect(markup).toContain('Experimental');

    expect(markup).not.toContain('93.135');
    expect(markup).not.toMatch(/PointNet\+\+[^<]*Default/);
  });

  // The accuracy panel showed one diameter error: 0.90 cm, from 65 isolated
  // trees in Belgium. That number is true and it is not the one this product
  // is about. TreeQ is aimed at tropical forest; the tropical cohort has been
  // measured — 61 trees felled and weighed in Cameroon — and the panel had no
  // way to say so, because scripts/sync_truth.py never emitted the block.
  //
  // A visitor reading 0.90 cm was reading a temperate figure as the accuracy
  // of a tropical product, and could not tell that the shipped gate refuses
  // 33 of the 60 measurable trees in the cohort that does apply.
  describe('the tropical cohort is not hidden behind the temperate one', () => {
    const cameroon = CORE_DEMO_EVIDENCE.validation.cameroon61;

    it('states the tropical diameter error beside the temperate one', () => {
      const markup = renderToStaticMarkup(<HomePage />);

      expect(markup).toContain(cameroon.dbhGateAppliedMaeCm.toFixed(2));
      expect(markup).toContain(
        CORE_DEMO_EVIDENCE.validation.demol65.dbhMaeCm.toFixed(2),
      );
    });

    it('says how many trees the gate refused', () => {
      const markup = renderToStaticMarkup(<HomePage />);

      // Without both counts the headline is an average over an unnamed
      // subset, and 27 of 60 reads as 60 of 60.
      expect(markup).toContain(String(cameroon.gatePassedTrees));
      expect(markup).toContain(String(cameroon.gateRefusedTrees));
    });

    it('names the cohort as tropical and destructively harvested', () => {
      const markup = renderToStaticMarkup(<HomePage />);

      expect(markup).toContain('เขตร้อน');
    });

    it('quotes no accuracy figure that is not in the generated evidence', () => {
      const markup = renderToStaticMarkup(<HomePage />);

      // The ungated mean error is cohort-specific, not an upper error bound.
      expect(markup).not.toContain('1.37 ซม. จากต้นไม้ 60');
    });

    it('distinguishes the cohort, measurable subset and ungated mean without inventing refusal causes', () => {
      const markup = renderToStaticMarkup(<HomePage />);

      expect(markup).toContain(`ทั้งหมด ${cameroon.trees} ต้น`);
      expect(markup).toContain(`วัดได้ ${cameroon.treesMeasured} ต้น`);
      expect(markup).toContain('ไม่ใช่ขอบบนของความผิดพลาด');
      expect(markup).not.toContain('ส่วนใหญ่เป็นต้นใหญ่ที่มีพูพอน');
      expect(markup).not.toContain('ขอบบนของขั้นวัดขนาด');
    });
  });

  it('renders the five evidence-led editorial beats', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup.split('data-editorial-beat=').length - 1).toBe(5);

    expect(markup).toContain('ข้อจำกัดของการสำรวจแบบเดิม');
    expect(markup).toContain('เป้าหมายของโครงการ');
    expect(markup).toContain('วิธีทำงาน');
    // Renamed with the dataset gallery. The test follows the page here: the
    // heading is the supervisor's wording and the page is the source of truth.
    expect(markup).toContain('ชุดข้อมูล (Dataset) ที่ใช้');
    expect(markup).toContain('ความแม่นยำ');
  });

  it('renders each editorial beat exactly once', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(
      markup.match(/data-editorial-beat="problem"/g)?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(/data-editorial-beat="objectives"/g)?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(/data-editorial-beat="journey"/g)?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(
        /data-editorial-beat="three-dimensional-evidence"/g,
      )?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(/data-editorial-beat="validation"/g)?.length ?? 0,
    ).toBe(1);
  });

  it('shows the three project objectives', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain('ลดอุปสรรคทางภูมิศาสตร์');
    expect(markup).toContain('ลดต้นทุนและเวลา');
    expect(markup).toContain('ยกระดับความโปร่งใส');
  });

  it('describes the real PLY point cloud shown in the hero', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    /*
     * useEffect ยังไม่ทำงานระหว่าง renderToStaticMarkup
     * จึงตรวจข้อความสถานะเริ่มต้นแทนตัว Canvas ที่โหลดภายหลังใน browser
     */
    expect(markup).toContain('กำลังโหลด Point Cloud');
    expect(markup).toContain('กำลังเตรียมข้อมูลสามมิติสำหรับแสดงผล');
  });

  it('keeps navigation and contentinfo outside the main landmark', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    const mainStart = markup.indexOf('<main');
    const mainEnd = markup.indexOf('</main>');

    expect(mainStart).toBeGreaterThan(-1);
    expect(mainEnd).toBeGreaterThan(mainStart);

    const main = markup.slice(mainStart, mainEnd);

    expect(main).not.toContain('<nav');
    expect(main).not.toContain('<footer');

    const siteHeader = markup.indexOf('<header data-tone');

    expect(siteHeader).toBeGreaterThan(-1);
    expect(siteHeader).toBeLessThan(mainStart);
    expect(main).not.toContain('<header data-tone');
    expect(markup.indexOf('<footer')).toBeGreaterThan(mainEnd);
  });

  it('offers a keyboard skip link that targets the main landmark', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(
      getAnchorHrefByLabel(markup, 'ข้ามไปยังเนื้อหาหลัก'),
    ).toBe('#main-content');

    expect(markup).toContain('id="main-content"');

    const skip = (
      markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? []
    ).find((tag) => tag.includes('#main-content'));

    expect(skip).toBeDefined();
    expect(skip).toContain('sr-only');
    expect(skip).toContain('focus:not-sr-only');
  });

  it('never sets Thai text in the monospace face', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    const monoWithText =
      /<(?:p|span|dt|dd)[^>]*class="[^"]*font-mono[^"]*"[^>]*>([^<]+)</g;

    const THAI = /[\u0E00-\u0E7F]/;
    const offenders: string[] = [];

    for (const match of markup.matchAll(monoWithText)) {
      const text = match[1].trim();

      if (THAI.test(text)) {
        offenders.push(text);
      }
    }

    expect(offenders).toEqual([]);
  });
});
