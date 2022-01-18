# IRT-Quiz
## What it does?
The web-app helps an organization to conduct multiple choice single correct quizzes (MCQ) where the questions are sorted mainly based on their difficulty value and the questions are not repetitive hence it minimizes the chances of academic misconduct. A simple recommender model is used to recommend the next
question according to the response to the previous question. It has a 'Comparision' section which will help to evaluate students' performance (understanding of the concept) on scale of 0-5.

## How it does?
A deep learning model uses inputs (present difficulty, response time, correctness of the response) to predict the next questions difficulty. The 'Comparison' section uses girth module an IRT package which takes inputs to evaluate the knowledge latent trait.

