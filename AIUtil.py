
import os
import requests

review_summary_prompt = "You are an assistant, generate summary for the following reviews about a book. The summary should " \
                 "be concise and capture the main points of the reviews. Highlight the positive and negative aspects " \
                 "mentioned by the reviewers. The summary should be in a neutral tone and should not include any " \
                 "personal opinions or additional information. return just the summary, do not add any additional " \
                 "information or text"

book_summary_prompt = "You are an assistant, generate summary for the following book. The summary should be concise and clear in plain english format, " \
                    "capturing the main points of the book. The summary should be in a neutral tone and should not include any " \
                    "personal opinions or additional information. return just the summary, do not add any additional " \
                    "information or text"


async def summarize_reviews(reviews):
    # call LLM to summarize the reviews
    url = os.getenv("llm_endpoint")+'/api/chat'
    headers = {
        "content-type": "application/json",
        "accept": "application/json"
    }
    reviews_consolidated = " ".join(reviews)
    print(reviews_consolidated)
    requestObj = {
        "model": "llama3.2",
        "messages": [{"role": "system",
                     "content": review_summary_prompt },
                    {"role": "user", "content": reviews_consolidated}],
        "stream": False
    }
    response = requests.post(url, headers=headers, json=requestObj)

    if response.status_code != 200:
        print("Error in generating summary")
        return "".join(reviews)
    print(response.content)
    return response.json().get("message").get("content")


async def generateSummary(content):
    # call LLM to generate summary
    url = os.getenv("llm_url")
    headers = {
        "content-type": "application/json",
        "accept": "application/json"
    }

    requestObj = {
        "model": "llama3.2",
        "message": [{"role": "system",
                     "content": book_summary_prompt},
                    {"role": "user", "content": content}],
        "stream": False
    }

    response = requests.post(url, headers=headers, json=requestObj)

    if (response.status_code != 200):
        print("Error in generating summary")
        return None
    response = response.json()
    summary_content = response.get("message").get("content")
    return summary_content

