import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import re
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))  # Replace with your actual Groq key


# ─────────────────────────────────────────────
# GROQ HELPER
# ─────────────────────────────────────────────
def ask_groq(prompt, max_tokens=500):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"


# ─────────────────────────────────────────────
# DYNAMIC TOPIC GENERATOR
# ─────────────────────────────────────────────
def generate_topic_from_ai(topic):
    """Generate each field separately to avoid JSON parsing issues"""

    # Step 1: Generate explanation
    explanation = ask_groq(
        f"In 2-3 sentences, explain what '{topic}' is in Machine Learning for a beginner. Include one real-world example. Only give the explanation text, nothing else.",
        max_tokens=200
    )

    # Step 2: Generate types/concepts
    types_raw = ask_groq(
        f"List exactly 5 subtypes or key concepts of '{topic}' in Machine Learning. Return only a numbered list like:\n1. item\n2. item\n3. item\n4. item\n5. item\nNothing else.",
        max_tokens=150
    )
    # Parse numbered list into array
    types = []
    for line in types_raw.strip().split('\n'):
        line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
        if line and len(line) > 2:
            types.append(line)
    types = types[:5] if len(types) >= 5 else types + [f"{topic} concept {i}" for i in range(len(types)+1, 6)]

    # Step 3: Generate Python code
    code = ask_groq(
        f"Write a simple, complete, runnable Python code example for '{topic}' in Machine Learning using scikit-learn. Only return the code, no explanation.",
        max_tokens=400
    )
    # Clean code block markers
    code = re.sub(r'```python|```', '', code).strip()

    # Step 4: Generate quiz questions one by one
    quiz = []
    for i in range(1, 4):
        q_raw = ask_groq(
            f"""Create quiz question number {i} about '{topic}' in Machine Learning.
Return ONLY this exact format:
QUESTION: your question here?
A: first option
B: second option
C: third option
D: fourth option
ANSWER: A""",
            max_tokens=150
        )
        # Parse the quiz question
        q_data = parse_quiz_question(q_raw)
        if q_data:
            quiz.append(q_data)

    # Fallback quiz if parsing failed
    if len(quiz) < 3:
        quiz = [
            {"question": f"What is {topic} mainly used for in ML?", "options": ["Prediction", "Data storage", "UI design", "Networking"], "answer": "Prediction"},
            {"question": f"Which Python library is used for {topic}?", "options": ["scikit-learn", "pygame", "tkinter", "requests"], "answer": "scikit-learn"},
            {"question": f"What type of learning does {topic} belong to?", "options": ["Machine Learning", "Manual coding", "Database design", "Networking"], "answer": "Machine Learning"}
        ]

    return {
        "explanation": explanation.strip(),
        "types": types,
        "code": code,
        "quiz": quiz
    }, True


def parse_quiz_question(raw):
    """Parse quiz response into structured dict"""
    try:
        lines = [l.strip() for l in raw.strip().split('\n') if l.strip()]
        question = ""
        options = []
        answer_letter = ""

        for line in lines:
            if line.upper().startswith("QUESTION:"):
                question = line.split(":", 1)[1].strip()
            elif re.match(r'^[ABCD][\.\:\)]\s', line):
                opt_text = re.sub(r'^[ABCD][\.\:\)]\s*', '', line).strip()
                options.append(opt_text)
            elif line.upper().startswith("ANSWER:"):
                answer_letter = line.split(":", 1)[1].strip().upper()[0]

        if question and len(options) == 4 and answer_letter in "ABCD":
            idx = "ABCD".index(answer_letter)
            return {
                "question": question,
                "options": options,
                "answer": options[idx]
            }
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
# STATIC TOPICS
# ─────────────────────────────────────────────
ml_topics = {
    "regression": {
        "explanation": "Regression is a supervised learning technique used to predict continuous values. It finds the relationship between input features (X) and output value (Y). Example: predicting house price, temperature, salary.",
        "types": ["Linear Regression", "Multiple Linear Regression", "Polynomial Regression", "Ridge Regression", "Lasso Regression"],
        "code": """from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

X = [[1],[2],[3],[4],[5]]
y = [2,4,6,8,10]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print("Predictions:", y_pred)
print("MSE:", mean_squared_error(y_test, y_pred))""",
        "quiz": [
            {"question": "Regression is mainly used for?", "options": ["Classification", "Predicting continuous values", "Clustering", "Dimensionality reduction"], "answer": "Predicting continuous values"},
            {"question": "Which is a regression evaluation metric?", "options": ["Accuracy", "Precision", "Mean Squared Error", "Recall"], "answer": "Mean Squared Error"},
            {"question": "Ridge Regression is used to reduce?", "options": ["Overfitting", "Underfitting", "Data imbalance", "Noise in images"], "answer": "Overfitting"},
            {"question": "What does slope represent in linear regression?", "options": ["Intercept", "Rate of change", "Error value", "Sample size"], "answer": "Rate of change"},
            {"question": "Which library is used for regression in Python?", "options": ["pygame", "scikit-learn", "tkinter", "PIL"], "answer": "scikit-learn"}
        ]
    },
    "classification": {
        "explanation": "Classification is a supervised learning technique used to predict categorical labels. It assigns input data into predefined classes. Example: spam/not spam, disease/no disease, cat/dog.",
        "types": ["Binary Classification", "Multi-class Classification", "Multi-label Classification", "Logistic Regression", "Random Forest"],
        "code": """from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

X = [[1],[2],[3],[4],[5],[6]]
y = [0,0,0,1,1,1]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
model = LogisticRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print("Predictions:", y_pred)
print("Accuracy:", accuracy_score(y_test, y_pred))""",
        "quiz": [
            {"question": "Classification is mainly used for?", "options": ["Predicting continuous values", "Predicting labels", "Clustering", "Sorting data"], "answer": "Predicting labels"},
            {"question": "Logistic Regression is used for?", "options": ["Regression", "Classification", "Clustering", "Dimensionality reduction"], "answer": "Classification"},
            {"question": "Which metric is used for classification?", "options": ["MSE", "RMSE", "Accuracy", "MAE"], "answer": "Accuracy"},
            {"question": "What is binary classification?", "options": ["Predicts 3 or more classes", "Predicts 2 classes only", "Predicts numbers", "Groups data"], "answer": "Predicts 2 classes only"},
            {"question": "Which algorithm builds decision boundaries?", "options": ["K-Means", "SVM", "PCA", "Apriori"], "answer": "SVM"}
        ]
    },
    "neural networks": {
        "explanation": "Neural Networks are computing systems inspired by the human brain. They consist of layers of interconnected nodes that learn patterns from data through training.",
        "types": ["Feedforward Neural Networks", "Convolutional Neural Networks CNN", "Recurrent Neural Networks RNN", "LSTM", "Transformers"],
        "code": """from sklearn.neural_network import MLPClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(n_samples=100, n_features=4, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500)
model.fit(X_train, y_train)
print("Accuracy:", model.score(X_test, y_test))""",
        "quiz": [
            {"question": "What inspired neural networks?", "options": ["DNA structure", "Human brain", "Sorting algorithms", "Cloud computing"], "answer": "Human brain"},
            {"question": "What is an activation function used for?", "options": ["Loading data", "Introducing non-linearity", "Splitting data", "Normalizing labels"], "answer": "Introducing non-linearity"},
            {"question": "CNN is mainly used for?", "options": ["Text data", "Time series", "Image data", "Tabular data"], "answer": "Image data"},
            {"question": "What is backpropagation?", "options": ["Forward pass", "Error correction through layers", "Data augmentation", "Feature selection"], "answer": "Error correction through layers"},
            {"question": "RNN is best suited for?", "options": ["Images", "Sequential and time data", "Clustering", "Regression only"], "answer": "Sequential and time data"}
        ]
    },
    "clustering": {
        "explanation": "Clustering is an unsupervised learning technique that groups similar data points without predefined labels. Example: customer segmentation, document grouping.",
        "types": ["K-Means Clustering", "Hierarchical Clustering", "DBSCAN", "Gaussian Mixture Models", "Agglomerative Clustering"],
        "code": """from sklearn.cluster import KMeans
import numpy as np

X = np.array([[1,2],[1,4],[1,0],[10,2],[10,4],[10,0]])
kmeans = KMeans(n_clusters=2, random_state=42)
kmeans.fit(X)

print("Labels:", kmeans.labels_)
print("Centroids:", kmeans.cluster_centers_)""",
        "quiz": [
            {"question": "Clustering is which type of learning?", "options": ["Supervised", "Unsupervised", "Reinforcement", "Semi-supervised"], "answer": "Unsupervised"},
            {"question": "K-Means requires you to specify?", "options": ["Labels", "Number of clusters", "Test size", "Learning rate"], "answer": "Number of clusters"},
            {"question": "What are centroids in K-Means?", "options": ["Outliers", "Center points of clusters", "Input features", "Loss values"], "answer": "Center points of clusters"},
            {"question": "DBSCAN is useful for?", "options": ["Linearly separable data", "Arbitrary shape clusters", "Image classification", "Text generation"], "answer": "Arbitrary shape clusters"},
            {"question": "Which metric evaluates clustering quality?", "options": ["Accuracy", "Silhouette Score", "MSE", "F1-Score"], "answer": "Silhouette Score"}
        ]
    },
    "decision trees": {
        "explanation": "A Decision Tree splits data into branches based on feature values. It is easy to understand and interpret, making it great for beginners in ML.",
        "types": ["Classification Tree", "Regression Tree", "Random Forest", "Gradient Boosting", "XGBoost"],
        "code": """from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

X = [[1,2],[2,3],[3,4],[4,5],[5,6],[6,7]]
y = [0,0,0,1,1,1]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
model = DecisionTreeClassifier(max_depth=3)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))""",
        "quiz": [
            {"question": "Decision Trees are which type of learning?", "options": ["Unsupervised", "Supervised", "Reinforcement", "None"], "answer": "Supervised"},
            {"question": "What does max_depth control?", "options": ["Number of features", "Tree size", "Learning rate", "Clusters"], "answer": "Tree size"},
            {"question": "Random Forest is made of?", "options": ["Single tree", "Multiple trees", "Neural layers", "Clusters"], "answer": "Multiple trees"},
            {"question": "Decision Trees are prone to?", "options": ["Underfitting", "Overfitting", "Clustering errors", "Low accuracy always"], "answer": "Overfitting"},
            {"question": "Which splitting criterion is used?", "options": ["Gradient", "Gini Impurity", "Silhouette", "MSE only"], "answer": "Gini Impurity"}
        ]
    },
    "ridge regression": {
        "explanation": "Ridge Regression uses L2 regularization to reduce overfitting by adding a penalty to large coefficients. It is ideal when features are correlated.",
        "types": ["L2 Regularization", "Ridge vs Lasso", "ElasticNet combined", "Regularization path", "Cross-validation for alpha"],
        "code": """from sklearn.linear_model import Ridge

X = [[1],[2],[3],[4],[5]]
y = [2,4,6,8,10]

model = Ridge(alpha=1.0)
model.fit(X, y)

print("Coefficient:", model.coef_)
print("Intercept:", model.intercept_)""",
        "quiz": [
            {"question": "Ridge Regression uses which regularization?", "options": ["L1", "L2", "L0", "None"], "answer": "L2"},
            {"question": "Ridge Regression is mainly used to reduce?", "options": ["Overfitting", "Underfitting", "Noise", "Missing values"], "answer": "Overfitting"},
            {"question": "The penalty term affects?", "options": ["Model coefficients", "Dataset size", "Class labels", "Accuracy directly"], "answer": "Model coefficients"},
            {"question": "What is the alpha parameter?", "options": ["Learning rate", "Regularization strength", "Train size", "Number of features"], "answer": "Regularization strength"},
            {"question": "Lasso uses which regularization?", "options": ["L2", "L1", "L0", "ElasticNet"], "answer": "L1"}
        ]
    }
}


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route("/ai_explain", methods=["POST"])
def ai_explain():
    data = request.json
    topic = data.get("topic", "")
    question = data.get("question", "")
    prompt = f"""You are a friendly ML tutor. A student is learning about '{topic}' and asks: '{question}'
Answer clearly in 3-5 sentences. Use a simple example if helpful."""
    return jsonify({"answer": ask_groq(prompt, 350)})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    topic = data.get("topic", "")
    level = data.get("level", "beginner")
    prompt = f"""You are an ML tutor. Explain '{topic}' for a {level} level student.
Include: 1) Simple definition 2) How it works 3) Real-world example 4) Key points to remember."""
    return jsonify({"result": ask_groq(prompt, 500)})


@app.route("/generator")
def generator():
    return render_template("generate.html")



@app.route("/audio")
def audio_page():
    return render_template("audio.html")


@app.route("/audio_explain", methods=["POST"])
def audio_explain():
    data = request.json
    topic = data.get("topic", "")
    prompt = f"""You are an ML teacher giving a clear spoken explanation of '{topic}'.
Explain it in a friendly, conversational way as if talking to a student.
Structure it as:
1. What is {topic}? (simple definition)
2. How does it work? (2-3 sentences)
3. Real world example (1 sentence)
4. Why is it important? (1 sentence)
Keep total response under 120 words. Use simple language. No bullet points, just flowing sentences."""
    text = ask_groq(prompt, max_tokens=200)
    return jsonify({"text": text})

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    topic_name = ""
    ai_generated = False

    if request.method == "POST":
        topic = request.form.get("topic", "").lower().strip()
        topic_name = topic.title()

        if topic in ml_topics:
            result = ml_topics[topic]
            ai_generated = False
        else:
            result, ai_generated = generate_topic_from_ai(topic)

    return render_template("index.html",
                           result=result,
                           topic_name=topic_name,
                           topics=list(ml_topics.keys()),
                           ai_generated=ai_generated)


if __name__ == "__main__":
    app.run(debug=True)
