var ctx = document.getElementById("calorieChart");

async function createCalorieChart() {

    var myLineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: timestamps,
        datasets: [{
          label: "Calories",
          yAxisID: 'A',
          fill: true,
          lineTension: 0.3,
          backgroundColor: "rgba(78, 115, 223, 0.25)",
          borderColor: "rgba(78, 115, 223, 1)",
          pointRadius: 0,
          pointBackgroundColor: "rgba(78, 115, 223, 1)",
          pointBorderColor: "rgba(78, 115, 223, 1)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
          pointHoverBorderColor: "rgba(78, 115, 223, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: goal_calories_in
        },
        {
          label: "Target Daily Caloric Intake",
          yAxisID: 'A',
          fill: true,
          lineTension: 0.3,
          backgroundColor: "rgba(255, 0, 0, 0.1)",
          borderColor: "rgba(255, 0, 0, 0.6)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(255, 0, 0, 0.20)",
          pointBorderColor: "rgba(255, 0, 0, 0.25)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(255, 0, 0, 1)",
          pointHoverBorderColor: "rgba(255, 0, 0, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: calories_in
        }],
      },
      options: {
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 10,
            right: 25,
            top: 25,
            bottom: 15
          }
        },
        scales: {
          xAxes: [{
            time: {
              unit: 'date'
            },
            gridLines: {
              display: false,
              drawBorder: false
            },
            ticks: {
              maxTicksLimit: 15
            }
          }],
          yAxes: [{
            id: 'A',
            position: 'left',
            scaleLabel: {
              display: true,
              labelString: 'Weight'
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
              zeroLineBorderDash: [2]
            }
          }],
        },
        legend: {
          display: false,
          position: 'bottom',
        },
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          titleMarginBottom: 10,
          titleFontColor: '#6e707e',
          titleFontSize: 14,
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 15,
          yPadding: 15,
          displayColors: false,
          intersect: false,
          mode: 'index',
          caretPadding: 10,
        }
      }
    });

};

createCalorieChart()
