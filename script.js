t quotes = [
	    { quote: "Curiosity is the spark behind every great idea.", author: "Unknown" },
	    { quote: "Stay curious, keep learning.", author: "Albert Einstein" },
	    { quote: "The best ideas emerge from curiosity and exploration.", author: "Marie Curie" },
	    { quote: "Curiosity fuels creativity.", author: "Leonardo da Vinci" },
	    { quote: "Never stop asking questions.", author: "Isaac Newton" }
];

function getNewQuote() {
	    const randomIndex = Math.floor(Math.random() * quotes.length);
	    const randomQuote = quotes[randomIndex];
	    document.getElementById("quote").textContent = `"${randomQuote.quote}"`;
	    document.getElementById("author").textContent = `- ${randomQuote.author}`;
}
