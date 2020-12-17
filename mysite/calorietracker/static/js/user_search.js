// Live Search Users for Adding Friends

// Input change small search bar or Small button click triggers this
function updateLiveSearchSm() {
  displaySearchNavTab()
  var searchQuery = document.getElementById("searchbarSm").value
  updateLiveSearch(searchQuery)
}

// Input change large search bar or Large button click triggers this
function updateLiveSearchLg() {
  displaySearchNavTab()
  var searchQuery = document.getElementById("searchbarLg").value
  updateLiveSearch(searchQuery)
}

// Display search nav tab
function displaySearchNavTab() {
  $('.nav-tabs a[href="#searchusers"]').tab('show')
}

// async fetch json
async function fetchUsers(searchQuery) {
  let apiURL = window.location.origin + '/api/usernames/' + searchQuery;
  // console.log(apiURL)
  const response = await fetch(apiURL);
  return response.json()
}

function updateLiveSearch(searchQuery) {
  if (searchQuery) {
    // Make Request to DRF api search endpoint asynchronously
    let searchResults = fetchUsers(searchQuery);

    searchResults.then(function (result) {
      if (result.length) { // if there are results...

        document.getElementById('ErrorText').innerHTML = ''; // remove any previous error text
        document.getElementById('search-results').innerHTML = ''; // reset search-results.innerHTML

        for (index = 0; index < result.length; index++) { // iteratively add result.username and form button to add user as friend
          if (result[index].username === username) { // don't display self
            continue;
          }
          if (all_friends.indexOf(result[index].username) > -1) { // filter results for usernames that are not already in all_friends
            continue
          }
          if (pending_outgoing_requests_usernames.indexOf(result[index].username) > -1) { // filter results for usernames that are not already in pending_outgoing_requests
            continue
          }

          // todo improve html building here so its more readable.
          let prof_url = "'/profile/" + result[index].username + "'"
          let form = '<form class="float-right"' + friend_request_action + '" method="POST">' + csrf + '<input type="hidden" id="id_to_user" name="to_user" value="' + result[index].id + '">' + button + '</form>'
          document.getElementById('search-results').innerHTML += ('<li class="dropdown-item mb-2 mt-2" style="display: inline-block;" onclick="location.href=' + prof_url + ';"><text style="text-decoration: none; font-size: 1.15rem;"">' + result[index].username + '</text>' + form + '</li>');
        }

      } else { // if there are no results...
        document.getElementById('ErrorText').innerHTML = ('No users found matching: ' + searchQuery);
      }
    })
  } else {
    document.getElementById('ErrorText').innerHTML = ('Search for a username above')
  }
}