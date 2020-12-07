
// This Assumes the get_cookie.js file has been loaded in and the csrftoken is accessable

// The below needs to happen somewhere before these functions cann be called
// const csrftoken = getCookie('csrftoken');

function hideAllNotifications() {

      var notifications = document.getElementsByClassName("notification");

      // HTMLCollection is returned by getElementsByClassName and getElementsByTagName but does not have a forEach method
      HTMLCollection.prototype.forEach = Array.prototype.forEach;

      // Remove all notifications in HTMLcollection
      notifications.forEach(function (element, i) {
            element.remove(element.selectedIndex)
      });

      // Reset badge counter
      var notifications_badge_counter = document.getElementById("notifications_badge_counter")
      notifications_badge_counter.remove(notifications_badge_counter)

}

function hideNotification(id) {

      // Remove Notification
      var notification = document.getElementById("notification" + id)
      notification.remove(notification)

      // Decrement Badge Counter
      var notifications_badge_counter = document.getElementById("notifications_badge_counter");
      var new_count = parseInt(notifications_badge_counter.innerText) - 1

      if (new_count == 0) {
            // If 0, remove counter alltogether
            notifications_badge_counter.remove(notifications_badge_counter)
      } else {
            notifications_badge_counter.innerText = new_count + "+";
      }


}


function clearAllNotifications() {

      fetch("/api/notifications/clear/", {
            method: 'PATCH',
            credentials: 'same-origin',
            headers: {
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
                  console.log("Cleared All Notifications")
            })

      hideAllNotifications();
};

function clearNotification(id) {

      fetch(`/api/notification/${id}/clear/`, {
            method: 'PATCH',
            credentials: 'same-origin',
            headers: {
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
            })

      hideNotification(id);
};
