// JavaScript ES6+ features

const API_VERSION = "1.0.0";

function calculateSum(a, b) {
    return a + b;
}

class Calculator {
    add(x, y) {
        return x + y;
    }

    static create() {
        return new Calculator();
    }
}

const arrowFunction = (a, b) => a + b;

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}