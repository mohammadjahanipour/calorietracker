
// This Assumes the get_cookie.js file has been loaded in and the csrftoken is accessable

// The below needs to happen somewhere before these functions cann be called
// const csrftoken = getCookie('csrftoken');

function clearAllNotifications() {

  fetch("/api/notifications/clear/", {
        method: 'PATCH',
        credentials: 'same-origin',
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', //Necessary to work with request.is_ajax()
            'X-CSRFToken': csrftoken,
    },
    })
    .then(response => {
          return response.json() //Convert response to JSON
    })
    .then(data => {
    //Perform actions with the response data from the view
    console.log("Cleared All Notification")
    console.log(data)
    })
};

function clearNotification(id) {

  fetch(`/api/notification/${id}/clear/`, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', //Necessary to work with request.is_ajax()
            'X-CSRFToken': csrftoken,
    },
    })
    .then(response => {
          return response.json() //Convert response to JSON
    })
    .then(data => {
    //Perform actions with the response data from the view
    console.log("Cleared Notification")
    console.log(data)
    })
};
