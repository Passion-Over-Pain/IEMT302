// Linear regression model for loan repayment duration prediction
// Formula: y = b + w₁·age + w₂·income + w₃·loan_amount + w₄·credit_score + w₅·current_debt + w₆·interest_rate

// Model weights (these would normally be trained on historical data)
const modelWeights = {
  bias: 25.0, // Base months
  age: -0.1, // Older people tend to repay faster (slightly negative weight)
  income: -0.0002, // Higher income leads to faster repayment (negative weight)
  loanAmount: 0.0015, // Larger loans take longer to repay (positive weight)
  creditScore: -0.05, // Higher credit score leads to faster repayment (negative weight)
  currentDebt: 0.0008, // More existing debt slows repayment (positive weight)
  interestRate: 0.8, // Higher interest rate extends repayment time (positive weight)
};

// Function to predict loan repayment duration
function predictRepaymentDuration(
  age,
  income,
  loanAmount,
  creditScore,
  currentDebt,
  interestRate
) {
  // Apply the linear regression formula
  let prediction =
    modelWeights.bias +
    modelWeights.age * age +
    modelWeights.income * income +
    modelWeights.loanAmount * loanAmount +
    modelWeights.creditScore * creditScore +
    modelWeights.currentDebt * currentDebt +
    modelWeights.interestRate * interestRate;

  // Ensure the prediction is positive
  return Math.max(1, prediction);
}

// Function to handle form submission
function handleFormSubmit(event) {
  event.preventDefault();

  // Get form values
  const age = parseFloat(document.getElementById("age").value);
  const income = parseFloat(document.getElementById("income").value);
  const loanAmount = parseFloat(document.getElementById("loanAmount").value);
  const creditScore = parseFloat(document.getElementById("creditScore").value);
  const currentDebt = parseFloat(document.getElementById("currentDebt").value);
  const interestRate = parseFloat(
    document.getElementById("interestRate").value
  );

  // Validate inputs
  if (
    isNaN(age) ||
    isNaN(income) ||
    isNaN(loanAmount) ||
    isNaN(creditScore) ||
    isNaN(currentDebt) ||
    isNaN(interestRate)
  ) {
    document.getElementById("durationResult").textContent =
      "Please fill in all fields with valid numbers.";
    return;
  }

  // Predict repayment duration
  const duration = predictRepaymentDuration(
    age,
    income,
    loanAmount,
    creditScore,
    currentDebt,
    interestRate
  );

  // Display result
  document.getElementById("durationResult").innerHTML = `${duration.toFixed(
    1
  )} months<br><span style="font-size: 0.9em;">(${(duration / 12).toFixed(
    1
  )} years)</span>`;
}

// Add event listener to form
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("loanForm");
  if (form) {
    form.addEventListener("submit", handleFormSubmit);
  }
});
