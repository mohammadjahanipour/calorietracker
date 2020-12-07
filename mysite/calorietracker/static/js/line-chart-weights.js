var ctx = document.getElementById("weightChart");

async function createWeightChart() {
  var myLineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: timestamps,
      datasets: [
        {
          label: "Weight",
          yAxisID: "A",
          fill: true,
          lineTension: 0.3,
          backgroundColor: "rgba(78, 115, 223, 0.05)",
          borderColor: "rgba(78, 115, 223, 1)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(78, 115, 223, .35)",
          pointBorderColor: "rgba(78, 115, 223, .35)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
          pointHoverBorderColor: "rgba(78, 115, 223, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: weights,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: 10,
          right: 25,
          top: 25,
          bottom: 15,
        },
      },
      scales: {
        xAxes: [
          {
            time: {
              unit: "date",
            },
            gridLines: {
              display: false,
              drawBorder: false,
            },
            scaleLabel: {
              display: false,
              labelString: "Date",
            },
            ticks: {
              maxTicksLimit: 15,
            },
          },
        ],
        yAxes: [
          {
            id: "A",
            position: "left",
            scaleLabel: {
              display: true,
              labelString: "Weight" + units_weight,
            },
            ticks: {
              maxTicksLimit: 10,
              reverse: false,
              padding: 10,
            },
            gridLines: {
              color: "rgb(234, 236, 244)",
              zeroLineColor: "rgb(234, 236, 244)",
              drawBorder: false,
              borderDash: [2],
              zeroLineBorderDash: [2],
            },
          },
        ],
      },
      legend: {
        display: false,
        position: "bottom",
      },
      tooltips: {
        backgroundColor: "rgb(255,255,255)",
        bodyFontColor: "#858796",
        titleMarginBottom: 10,
        titleFontColor: "#6e707e",
        titleFontSize: 14,
        borderColor: "#dddfeb",
        borderWidth: 1,
        xPadding: 15,
        yPadding: 15,
        displayColors: false,
        intersect: false,
        mode: "index",
        callbacks: {
          label: function (tooltipItems, data) {
            return tooltipItems.yLabel + units_weight;
          },
        },
        caretPadding: 10,
      },
    },
  });

  document.getElementById("downloadWC").addEventListener("click", function () {
    /*Get image of canvas element*/
    var url_base64jp = document
      .getElementById("weightChart")
      .toDataURL("image/jpg");
    /*get download button (tag: <a></a>) */
    /*insert chart image url to download button (tag: <a></a>) */
    document.getElementById("downloadWC").href = url_base64jp;
  });
}

createWeightChart();
