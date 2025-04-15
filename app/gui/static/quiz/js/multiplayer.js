const gameContainer = document.getElementById('game-container');
const room_code = gameContainer.getAttribute('room-code');
const username = gameContainer.getAttribute('username');
const quiz = gameContainer.getAttribute('quiz');
const player = gameContainer.getAttribute('player');

console.log("Intilializing WebSocket connection");
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const quizSocket = new WebSocket(protocol + window.location.host + '/ws/multiplayer/' + room_code + '/');


quizSocket.onopen = function (event) {
    console.log('WebSocket connection established:', event);
};

quizSocket.onclose = function (event) {
    console.log('WebSocket connection closed:', event);
    console.log('Reason:', event.reason || 'No reason provided');
    console.log('Was clean:', event.wasClean);
    console.log('Code:', event.code);
};

quizSocket.onerror = function (event) {
    console.error('WebSocket error:', event);
};

quizSocket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log('Received data: ', data);

    if (data.type === 'start_game') {
        console.log("in start_game");
        document.getElementById('start-quiz').addEventListener('click', function (event) {
            event.preventDefault()

            console.log("in start_game");
            quizSocket.send(JSON.stringify({
                type: 'start_game',
                room_code: room_code,
                username: username
            }));
        });
    }
    else if (data.type === 'show_question') {
        // We want to display the question in the question-container div
        // We can use the fetch API to get the question data from the server
        // We hide all the elements in the body and append the questionContainer to the body
        // We use querySelectorAll to select all elements in the body and hide them
        // We use the createElement method to create a new div element for the questionContainer
        // and then we use the innerHTML property to set the content of the questionContainer div
        // We use the appendChild method to add the questionContainer to the body

        console.log("in show_question");
        const questionUrl = data.question.url;
        if (questionUrl) {
            fetch(questionUrl)
                .then(response => response.text())
                .then(html => {
                    // Using querySelectorAll to select all elements, expect the game-container, in the body and remove them
                    document.querySelectorAll('body > *:not(#game-container)').forEach(element => {
                        //element.style.display = 'none';
                        element.remove();
                    });
                    // We create a new div element to display the question(the element question-container will be put here)
                    const questionContainer = document.getElementById('question-container');
                    if (questionContainer) {
                        questionContainer.innerHTML = html;
                    } else {
                        const newContainer = document.createElement('div');
                        newContainer.id = 'question-container';
                        newContainer.innerHTML = html;
                        // We append the questionContainer to the body
                        document.body.appendChild(newContainer);
                    }

                    const nextQuestionButton = document.getElementById('next-question-button');

                    if (nextQuestionButton) {
                        nextQuestionButton.addEventListener('click', function (event) {
                            event.preventDefault()
                            console.log("in next_question");

                            const selectedAnswers = document.querySelectorAll('input[type="checkbox"]:checked, input[type="radio"]:checked');
                            const answersIds = Array.from(selectedAnswers).map(answer => answer.value);
                            console.log("answersIds:", answersIds);

                            if (answersIds.length === 0) {
                                alert("Please select at least one answer before submitting.");
                                return;
                            }

                            quizSocket.send(JSON.stringify({
                                type: 'submit_answer',
                                room_code: room_code,
                                username: username,
                                answer_ids: answersIds
                            }));
                        });
                    }

                    const finishButton = document.getElementById('finish-button');

                    if (finishButton) {
                        finishButton.addEventListener('click', function (event) {
                            event.preventDefault()
                            console.log("in finish_question");

                            const selectedAnswers = document.querySelectorAll('input[type="checkbox"]:checked, input[type="radio"]:checked');
                            const answersIds = Array.from(selectedAnswers).map(answer => answer.value);
                            console.log("answersIds:", answersIds);

                            if (answersIds.length === 0) {
                                alert("Please select at least one answer before submitting.");
                                return;
                            }

                            quizSocket.send(JSON.stringify({
                                type: 'submit_answer',
                                room_code: room_code,
                                username: username,
                                answer_ids: answersIds
                            }));
                        });
                    }
                })
                .catch(error => console.error('Error fetching question data: ', error));
        }
    } else if (data.type === 'show_results') {
        console.log("in show_results");
        // We want to display the results in the results-container div
        // We remove all the elements in the body and append the resultsContainer to the body

        document.querySelectorAll('body > *:not(#game-container)').forEach(element => {
            //element.style.display = 'none';
            element.remove();
        });

        console.log("data.results:", data.results);
        fetch(`/multiplayer_leaderboard/?results=${encodeURIComponent(JSON.stringify(data.results))}`)
            .then(response => response.text())
            .then(leaderboardMultiplayerHtml => {
                const leaderboard_container = document.createElement('div');
                leaderboard_container.id = 'leaderboard-container';
                leaderboard_container.innerHTML = leaderboardMultiplayerHtml;
                document.body.appendChild(leaderboard_container);
            })
            .catch(error => console.error('Error fetching header data: ', error));
    }
};
