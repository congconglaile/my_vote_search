#coding:utf-8
import json
import logging
import os
from datetime import timedelta
from typing import List

from flask import Flask, request, url_for

from my_config import PROMPT_TEMPLATE, HTML_RESOURCE_PATH
from vector_store.vs_tool import get_ref_docs_from_vs

app = Flask(__name__)

@app.route('/')
def index():
    return 'This is for PA vote search'



CANDIDATE_1_VS_ID = "./vector_store/vote_4"


def get_video_ts(ref_file_name, ref_text):
    print(f"### ref_file_name: {ref_file_name}")
    ref_file_name = ref_file_name.replace('.txt', '')
    print(f"### ref_file_name replace: {ref_file_name}")
    logging.info(f"### ref_file_name replace: {ref_file_name}")
    video_path = 'resource/video'
    json_path = 'resource/json'

    video_file = 'Trump_v_Biden_The_Final_Debate.mp4'
    json_file = 'resource/json/Trump_v_Biden_The_Final_Debate.json'

    for root, dirs, files in os.walk(video_path):
        for file in files:
            if file.find(ref_file_name) > -1:
                print(f"video path: {root}/{file}")
                video_file = file
                break
    for root, dirs, files in os.walk(json_path):
        for file in files:
            if file.find(ref_file_name) > -1 and file.find('.json') > -1:
                print(f"json path: {root}/{file}")
                json_file = f"{root}/{file}"
                break

    with open(json_file, encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
        context = data['text']
        segments = data['segments']

        start_idx = context.find(ref_text)
        start_ts = None
        if start_idx > -1:
            str_appender = ''
            for seg in segments:
                str_appender += seg['text']
                if len(str_appender) > start_idx:
                    start_ts = seg['start']
                    break
    print(f"video: {video_file}, text: {json_file}, start timestamp: {start_ts}")
    return video_file, start_ts, ref_text



@app.route('/display_video', methods=['GET'])
def display_video():
    args = request.args
    video_file = args['video_file']
    start_ts = max([float(args['start_ts'])-1, 0])
    logging.info(f"Video file: {video_file}, start timestamp: {start_ts}")

    return f"""
        <div style="text-align:center">
            <br><br>
            <video id="video1" width="1280" height="720" controls>
                <source src="{url_for('resource', filename='video/'+video_file)}" type="video/mp4">
            </video>
        </div>
    """


def get_html_ref(ref_file_name, ref_text):
    text_path = HTML_RESOURCE_PATH + ref_file_name
    url = ''
    title = ''
    with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().rsplit()
        content = ''.join(content)
        url = 'https://m.thepaper.cn/baijiahao_16210403'
        title = '首届数字金融前沿学术会议举办'
        # ref_text = re.sub(r'<url>(.*?)</url>', '', ref_text, flags=re.DOTALL)
        return url, title, ref_text


def generate_prompt(related_docs: List[str],
                    query: str,
                    prompt_template=PROMPT_TEMPLATE) -> str:
    html_docs = []
    context = ''
    source_documents = []
    ref_number = 0

    for inum, doc in enumerate(related_docs):
        doc_name = os.path.split(doc.metadata['source'])[-1]
        candidate_name = doc_name[:doc_name.index('_')]
        page_content = doc.page_content
        score = round(float(doc.metadata['score']), 2)
        print(f"--- doc: {doc_name}, score: {score} ---")

        if(doc_name.startswith('html_')):
            if(doc_name not in html_docs):
                ref_number += 1
                # html_docs.append(doc_name)
                url, title, ref_text = get_html_ref(doc_name, page_content)
                doc = {'type': 'html', 'candidate': 'candidate_name', 'url': url, 'title': title, 'content': page_content,
                       'score': score}
                source_documents.append(doc)
        else:
            ref_number += 1
            context += f"{ref_number}. {doc.page_content}\n"
            video_file, start_ts, ref_text = get_video_ts(doc_name, page_content)
            if start_ts:
                start_td = timedelta(seconds=start_ts)

                doc = {'type': 'video', 'candidate': 'candidate_name', 'url': f'http://localhost:5000/display_video?video_file={video_file}&start_ts={start_ts}',
                       'title': video_file, 'content': ref_text, 'score': score, 'start_ts': start_ts}
                source_documents.append(doc)
            # source_documents += f"""<br>{ref_number}. <a href='http://localhost:5000/display_video?video_file={video_file}&start_ts={start_ts}' target='_blank'>{video_file}</a>: {ref_text}(timestamp: {str(start_td)})"""
    prompt = prompt_template.replace("{question}", query).replace(f"{context}", context)
    return prompt, source_documents[0]


@app.route('/candidate', methods=['GET'])
def candidate1():
    args = request.args
    question = args['question']
    print(f"Question for candidate: {question}")
    docs = get_ref_docs_from_vs(question, CANDIDATE_1_VS_ID)
    prompt, source_docs = generate_prompt(docs, question)

    return source_docs


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

# http://localhost:5000/candidate?question=how%20to%20build%20a%20great%20school
