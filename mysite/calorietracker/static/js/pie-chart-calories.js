// Set new default font family and font color to mimic Bootstrap's default styling
(Chart.defaults.global.defaultFontFamily = "Nunito"),
  '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = "#858796";

// Pie Chart Example
var ctx = document.getElementById("piechartCalories");
var myPieChart = new Chart(ctx, {
  type: "doughnut",
  data: {
    labels: pie_labels,
    datasets: [
      {
        data: [pie_cal_in_red, pie_cal_in_green, pie_cal_in_yellow],
        backgroundColor: ["#DC143C", "#3CB371", "#cadf4f"],
        hoverBackgroundColor: ["#ad102f", "#2f8d59", "#cadf4f"],
        hoverBorderColor: "rgba(234, 236, 244, 1)",
      },
    ],
  },
  options: {
    maintainAspectRatio: false,
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      borderColor: "#dddfeb",
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      caretPadding: 10,
    },
    legend: {
      display: true,
      position: "bottom",
    },
    cutoutPercentage: 60,
    circumference: 2 * Math.PI,
    rotation: -2 * Math.PI,
  },
});

document.getElementById("downloadCIPC").addEventListener("click", function () {
  /*Get image of canvas element*/
  var url_base64jp = document
    .getElementById("piechartCalories")
    .toDataURL("image/jpg");
  /*get download button (tag: <a></a>) */
  /*insert chart image url to download button (tag: <a></a>) */
  document.getElementById("downloadCIPC").href = url_base64jp;
});
