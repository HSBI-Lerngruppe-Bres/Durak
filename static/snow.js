// JavaScript code to dynamically add snowflakes (if needed for more advanced effects)
(function() {
    const numberOfSnowflakes = 10;
    const snowflakesContainer = document.querySelector('.snowflakes');
    for (let i = 0; i < numberOfSnowflakes; i++) {
        const snowflake = document.createElement('div');
        snowflake.className = 'snowflake';
        snowflake.innerHTML = '❅';
        snowflake.style.left = Math.random() * 100 + '%';
        snowflake.style.animationDuration = Math.random() * 3 + 7 + 's';
        snowflake.style.animationDelay = Math.random() * 5 + 's';
        snowflakesContainer.appendChild(snowflake);
    }
})();
