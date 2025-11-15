#!/usr/bin/env python
# coding: utf-8

# In[2]:


from openai import OpenAI
import streamlit as st


# In[ ]:


#check current directory
import os
os.getcwd()


# In[3]:


f = open("keys/openaiapikey.txt")
OPENAI_API_KEY=f.read()


# In[4]:


model= OpenAI(api_key=OPENAI_API_KEY)


# In[6]:


st.title("My First AI chatbot")
#Inistializing memory in session state

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "memory" not in st.session_state:
    st.session_state["memory"] = []

st.chat_message("assistant").write("Hi,how can I help you?")

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input()

if user_input:
    # add user input to memory for context retention (eg :when we use chat gpt we prefer chatgpt to have memory of previous questions when we ask many subquestions for one question itself )
    st.session_state["messages"].append({"role":"user","content":user_input})
    if "my name is" in user_input.lower():
        name=user_input.split("my name is")[-1].strip().split([0])
        st.session_state["memory"]["name"] = name
        response_text = f"Nice to meet you,{name}!"
    else:
        # include memory in system prompt
        memory_content = (
            f"User's name is {st.session_state['memory'].get('name','Unknown')}"
            if "name" in st.session_state['memory'] else ""
        )
        response = model.chat.completions.create(
                   model='gpt-4o-mini', messages= [{'role':'system',
                   "content":f"""You are a professional educational
                   counsellor working in a data science Institute called "Learnbay".If someone asks your name,tell them politely that your name is "Learnbay soldier".{memory_content}"""}]+
                   st.session_state['messages'] + [{'role':'system',
                   "content":user_input}]
                           )
        response_text = response.choices[0].message.content     

    st.chat_message("assistant").write(response_text)
    st.session_state["messages"].append({"role":"user","content":user_input})
    st.session_state["memory"].append({"role":"user","content":user_input})

