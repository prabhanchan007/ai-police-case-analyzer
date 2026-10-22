// Basic JavaScript for the AI Police Case Analyzer.
// - Form page: sample data button and a "please wait" state on submit.
// - Report page: Download PDF and Download Image (both made locally in the browser
//   with html2canvas and jsPDF, which are bundled in static/js).

document.addEventListener("DOMContentLoaded", function () {
  setupFormPage();
  setupReportPage();
});

/* ---------------- Form page ---------------- */
function setupFormPage() {
  var form = document.getElementById("case-form");
  if (!form) return;

  var sampleBtn = document.getElementById("sample-btn");
  var generateBtn = document.getElementById("generate-btn");

  // Entirely fictional demonstration data.
  var sample = {
    case_ref: "FIC-2026-001",
    incident_date: "2026-10-20",
    incident_time: "16:30",
    location: "Fictional Market Road, Sample City",
    station: "Sample Town Police Station",
    officer: "Sub-Inspector (sample)",
    incident_type: "Theft",
    description: "The complainant states that a mobile phone was stolen from the shop counter while the shop owner was attending to another customer. The phone was taken without permission and the person left the shop quickly.",
    circumstances: "The shop was crowded at the time. The counter was unattended for a short while.",
    complainant: "Fictional Complainant A, shop owner",
    suspect: "Unknown person, reportedly wearing a grey jacket",
    witness: "Fictional Customer B was present in the shop",
    evidence: "CCTV camera above the shop entrance; purchase invoice of the phone",
    observations: "The shop owner noticed the phone was missing at about 4:30 pm."
  };

  sampleBtn.addEventListener("click", function () {
    Object.keys(sample).forEach(function (name) {
      var field = form.elements[name];
      if (field) field.value = sample[name];
    });
  });

  form.addEventListener("submit", function () {
    generateBtn.disabled = true;
    generateBtn.textContent = "Generating...";
  });
}

/* ---------------- Report page ---------------- */
function setupReportPage() {
  var report = document.getElementById("report");
  if (!report) return;

  var pdfBtn = document.getElementById("pdf-btn");
  var pngBtn = document.getElementById("png-btn");
  var msg = document.getElementById("export-msg");

  function setBusy(busy, text) {
    pdfBtn.disabled = busy;
    pngBtn.disabled = busy;
    msg.textContent = text || "";
  }

  function fileBase() {
    var ref = report.getAttribute("data-case-ref") || "case-report";
    return "case-report-" + ref.replace(/[^A-Za-z0-9_-]+/g, "_");
  }

  // Draw the whole report (not just the visible part) onto one canvas.
  // Also returns the vertical position of each section so the PDF can
  // start new pages between sections instead of cutting text in half.
  function renderReport() {
    report.classList.add("exporting");
    return html2canvas(report, {
      scale: 2,
      backgroundColor: "#ffffff",
      useCORS: true,
      logging: false,
      windowWidth: report.scrollWidth
    }).then(function (canvas) {
      var scale = canvas.width / report.offsetWidth;
      var top = report.getBoundingClientRect().top;
      var breaks = Array.prototype.map.call(
        report.querySelectorAll(".rsec"),
        function (s) { return Math.round((s.getBoundingClientRect().top - top) * scale); }
      );
      report.classList.remove("exporting");
      return { canvas: canvas, breaks: breaks };
    }).catch(function (err) {
      report.classList.remove("exporting");
      throw err;
    });
  }

  function downloadPng() {
    setBusy(true, "Creating image...");
    renderReport().then(function (r) {
      var link = document.createElement("a");
      link.download = fileBase() + ".png";
      link.href = r.canvas.toDataURL("image/png");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setBusy(false, "Image downloaded.");
    }).catch(function (err) {
      console.error(err);
      setBusy(false, "Sorry, the image could not be created.");
    });
  }

  function downloadPdf() {
    setBusy(true, "Creating PDF...");
    renderReport().then(function (r) {
      var canvas = r.canvas;
      var pdf = new window.jspdf.jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });

      var pageW = 210, pageH = 297, margin = 10;
      var imgW = pageW - 2 * margin;
      var pxPerMm = canvas.width / imgW;
      var pagePx = Math.floor((pageH - 2 * margin) * pxPerMm);

      var start = 0;
      var pages = 0;
      while (start < canvas.height) {
        var end = Math.min(start + pagePx, canvas.height);

        // If the page would end inside a section, end it at the last section
        // boundary that still fits (as long as that fills a fair part of the page).
        if (end < canvas.height) {
          var fits = r.breaks.filter(function (b) {
            return b > start + pagePx * 0.4 && b <= end;
          });
          if (fits.length) end = Math.max.apply(null, fits);
        }

        var sliceH = end - start;
        var slice = document.createElement("canvas");
        slice.width = canvas.width;
        slice.height = sliceH;
        var ctx = slice.getContext("2d");
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, slice.width, slice.height);
        ctx.drawImage(canvas, 0, start, canvas.width, sliceH, 0, 0, canvas.width, sliceH);

        if (pages > 0) pdf.addPage();
        pdf.addImage(slice.toDataURL("image/png"), "PNG", margin, margin, imgW, sliceH / pxPerMm);

        start = end;
        pages++;
      }

      // Footer with page numbers
      pdf.setFontSize(8);
      pdf.setTextColor(100);
      for (var i = 1; i <= pages; i++) {
        pdf.setPage(i);
        pdf.text("Draft - Requires Review  |  Page " + i + " of " + pages, pageW / 2, pageH - 5, { align: "center" });
      }

      pdf.save(fileBase() + ".pdf");
      setBusy(false, "PDF downloaded.");
    }).catch(function (err) {
      console.error(err);
      setBusy(false, "Sorry, the PDF could not be created.");
    });
  }

  pdfBtn.addEventListener("click", downloadPdf);
  pngBtn.addEventListener("click", downloadPng);
}
