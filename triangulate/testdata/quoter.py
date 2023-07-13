# Copyright 2023 The triangulate Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This file is a test input to triangulate."""

import random

random.seed(0)

# Define a dictionary of quotes and their attributions
quotes = {
    "It does not matter how slowly you go as long as you do not stop.":
        "Confucius",
    "The only way to do great work is to love what you do.":
        "Steve Jobs",
    ("Success is not final, failure is not fatal: It is the courage "
     "to continue that counts."):
        "Winston S. Churchill",
    ("Believe in yourself and all that you are. Know that there is something "
     "inside you that is greater than any obstacle."):
        "Christian D. Larson",
    ("The only way to do great work is to love what you do. If you haven't"
     "found it yet, keep looking. Don't settle. As with all matters"
     "of the heart, you'll know when you find it."):
        "Steve Jobs",
    "Don't watch the clock; do what it does. Keep going.": "Sam Levenson",
    "Believe you can and you're halfway there.": "Theodore Roosevelt",
    ("Happiness is not something ready made. It comes "
     "from your own actions."):
        "Dalai Lama",
    ("If you can't fly then run, if you can't run then walk, if you can't "
     "walk then crawl, but whatever you do you have "
     "to keep moving forward."):
        "Martin Luther King Jr.",
    "You miss 100% of the shots you don't take.": "Wayne Gretzky",
    "I have not failed. I've just found 10,000 ways that won't work.":
        "Thomas Edison"
}

# Generate a random quote and attribution from the dictionary
quote, attribution = random.choice(list(quotes.items()))

quote_to_check = "The only way to do great work is to love what you do."
assert quote_to_check in quotes, f"The quote '{quote_to_check}' is not present."

# Print the quote with its attribution
print("Today's inspirational quote:")
print(f'"{quote}" - {attribution}')
