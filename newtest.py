import openai
import streamlit as st
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit UI Enhancements
st.set_page_config(page_title="Pharma Society QnA Report Generator", page_icon="💊")

# Inline CSS for styling
st.markdown(
    """
    <style>
        /* General app styles */
        body {
            background-color: #f9f9f9;
            font-family: "Arial", sans-serif;
        }
        .main-header {
            font-size: 3rem;
            color: #FFA500;
            text-align: center;
            margin-bottom: 1rem;
            animation: fadeIn 6s;
        }
        .prompt-buttons button {
            background-color: #007bff;
            color: white;
            border: none;
            font-size: 1rem;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 5px;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.3s;
        }
        .prompt-buttons button:hover {
            background-color: #0056b3;
            transform: scale(1.05);
        }
        .table-container {
            margin: 20px 0;
        }
        .table-container .stDataFrame {
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .download-btn {
            display: inline-block;
            background-color: #28a745;
            color: white;
            padding: 10px 20px;
            font-size: 1rem;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
            transition: background-color 0.3s, transform 0.3s;
        }
        .download-btn:hover {
            background-color: #218838;
            transform: scale(1.05);
        }
        .fadeIn {
            animation: fadeIn 2s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Pharma Society Q&A Generator Section
st.markdown('<div class="main-header">💊 Pharma Society QnA Report Generator</div>', unsafe_allow_html=True)
st.write("🔬 This Q&A generator allows users to fetch answers to predefined queries about pharmaceutical societies by entering the society name in the text box. It uses OpenAI to generate answers specific to the entered society and displays them in a tabular format. Users can download this report as an Excel file.")

# Initialize session state
if "selected_societies" not in st.session_state:
    st.session_state.selected_societies = []
if "report_data" not in st.session_state:
    st.session_state.report_data = pd.DataFrame(columns=[
        "Society Name", "Membership Count", "Community Sites",
        "Influential on Policy", "Engagement with Leadership",
        "Clinical Trial Recruitment", "Engagement with Payors",
        "Area Experts on Board", "Therapeutic Research Collaborations",
        "Top Experts on Board", "Region"
    ])

# Define static answers
static_answers = {
    "FLASCO (Florida Society of Clinical Oncology)": {
        "Membership Count": 4100,
        "Community Sites": "Yes, FLASCO does encompasses community sites. FLASCO primarily focuses on academic and institutional settings for oncology practices.",
        "Influential on Policy": "No, FLASCO primarily focuses on education and advocacy within the field of clinical oncology, rather than having a direct influence on state or local policy.",
        "Engagement with Leadership": "Yes, FLASCO provides engagement opportunity with leadership. FLASCO offers various leadership development programs, opportunities to interact with leaders in the field, and chances to participate in decision-making processes within the organization.",
        "Clinical Trial Recruitment": "Yes, FLASCO provides support for clinical trial recruitment.",
        "Engagement with Payors": "Yes, FLASCO does provides engagement opportunities with payors. FLASCO primarily focuses on oncologists and cancer care in Florida.",
        "Area Experts on Board": "Yes, FLASCO includes area experts on its board. The board primarily consists of oncologists, pharmacists, and other professionals in the field of oncology.",
        "Therapeutic Research Collaborations": "Yes, FLASCO is involved in therapeutic research collaborations. FLASCO regularly partners with pharmaceutical companies and research institutions to conduct clinical trials and research studies aimed at advancing cancer treatment.",
        "Top Experts on Board": "Yes, FLASCO includes top therapeutic area experts on its board. FLASCO's mission is to improve the quality of care for oncology patients in Florida, and having top experts on the board helps to ensure that the best practices and advancements in the field are being implemented.",
        "Region": "Florida"
    },
    "GASCO (Georgia Society of Clinical Oncology)": {
        "Membership Count": 1900,
        "Community Sites": "Yes, GASCO actively engages with community oncology sites across Georgia to ensure the dissemination of best practices and resources to healthcare providers statewide.",
        "Influential on Policy": "Yes, GASCO collaborates with state and local policymakers to influence healthcare policies that benefit oncology care and cancer patients in Georgia.",
        "Engagement with Leadership": "Yes, GASCO provides engagement opportunity with leadership through various conferences, events, and committees that allow members to interact and collaborate with leaders in the field of clinical oncology.",
        "Clinical Trial Recruitment": "Yes, GASCO has established partnerships with research institutions to promote clinical trial awareness and streamline the recruitment process for oncology patients within Georgia.",
        "Engagement with Payors": "No, GASCO does not provide engagement opportunities with payors. GASCO's primary focus is on clinical oncology and supporting oncology professionals, rather than engaging with payors.",
        "Area Experts on Board": "Yes, GASCO includes area experts on its board, as it is a society of clinical oncologists in Georgia who would have expertise in the field.",
        "Therapeutic Research Collaborations": "Yes, GASCO is involved in therapeutic research collaborations. The organization collaborates with academic institutions, pharmaceutical companies, and other healthcare organizations to advance cancer care through research efforts.",
        "Top Experts on Board": "No, the GASCO board does not include top therapeutic area experts. GASCO is a professional organization for oncology professionals in Georgia, but it does not specifically focus on therapeutic area experts on its board.",
        "Region": "Georgia"
    },
    "IOS (Indiana Oncology Society)": {
        "Membership Count": 800,
        "Community Sites": "Yes, IOS encompasses community sites. There are community oncology practices included in the Indiana Oncology Society.",
        "Influential on Policy": "No, IOS is primarily focused on education and collaboration among oncology professionals in Indiana, and does not have a direct impact on state or local policy.",
        "Engagement with Leadership": "Yes, IOS provides opportunities for engagement with leadership, IOS organizes events, conferences, and meetings that allow members to interact and engage with leaders in the oncology field.",
        "Clinical Trial Recruitment": "No, IOS does not provide support for clinical trial recruitment. IOS focuses on education, advocacy, and networking for oncology professionals in Indiana.",
        "Engagement with Payors": "No, IOS does not provide engagement opportunities with payors, as it is focused on oncology-related activities",
        "Area Experts on Board": "Yes, The Indiana Oncology Society includes area experts on its board to ensure that the organization has access to a diverse range of expertise and perspectives in the field of oncology.",
        "Therapeutic Research Collaborations": "Yes, IOS is involved in therapeutic research collaborations. IOS regularly collaborates with various research organizations and institutions to advance cancer treatment methods and options.",
        "Top Experts on Board": "No, IOS does not include top therapeutic area experts on its board. IOS is a state-level organization for oncology professionals in Indiana and may not have the same level of expertise as other national organizations.",
        "Region": "Indiana"
    },
    "MOASC (Medical Oncology Association of Southern California)": {
        "Membership Count": 600,
        "Community Sites": "Yes, MOASC encompasses community sites as it represents medical oncologists in Southern California, including those practicing in community settings.",
        "Influential on Policy": "No, the organization focuses on education and networking for medical professionals in Southern California and does not have a primary focus on policy advocacy.",
        "Engagement with Leadership": "Yes, MOASC provides engagement opportunities with leadership through various events, conferences, and programs where members can interact with and learn from leaders in the field of medical oncology.",
        "Clinical Trial Recruitment": "No, MOASC does not provide support for clinical trial recruitment. , MOASC primarily focuses on providing education and networking opportunities for medical oncology professionals in Southern California.",
        "Engagement with Payors": "No, MOASC does not provide engagement opportunities with payors. This organization primarily focuses on providing education, resources, and support for medical oncologists in Southern California.",
        "Area Experts on Board": "Yes, , MOASC includes area experts on its board.",
        "Therapeutic Research Collaborations": "Yes, MOASC is involved in therapeutic research collaborations, as they work with various partners to advance cancer treatments.",
        "Top Experts on Board": "Yes, MOASC includes top therapeutic area experts on its board., The organization consists of medical oncologists and hematologists who specialize in various areas of cancer treatment.",
        "Region": "California"
    },
    "IOWA Oncology Society": {
        "Membership Count": 2200,
        "Community Sites": "Yes, The IOWA Oncology Society focuses on community sites. Their main focus is on the community sites.",
        "Influential on Policy": "No, lack of public information on direct influence on policy.",
        "Engagement with Leadership": "Yes, The IOWA Oncology Society provides engagement opportunities with leadership through networking events, leadership development programs, and participation in committees and task forces.",
        "Clinical Trial Recruitment": "Yes, IOWA Oncology Society provides support for clinical trial recruitment.",
        "Engagement with Payors": "No, The IOWA Oncology Society does not provide engagement opportunities with payors. The organization primarily focuses on professional development and support for oncology professionals in Iowa.",
        "Area Experts on Board": "Yes, The IOWA Oncology Society includes area experts on its board because they are specialists in their field who provide expertise and guidance on cancer treatment and research.",
        "Therapeutic Research Collaborations": "Yes, this organization is involved in therapeutic research collaborations. Iowa Oncology Society actively collaborates with industry partners and academic institutions to advance research in the field of oncology.",
        "Top Experts on Board": "Yes, the IOWA Oncology Society includes top therapeutic area experts on its board. Members are typically oncologists and other healthcare professionals with expertise in cancer treatment.",
        "Region": "Iowa"
    }
}

# Step 1: Filter dropdown options
all_societies = list(static_answers.keys())
available_societies = [society for society in all_societies if society not in st.session_state.selected_societies]
society_name = st.selectbox("Select the Pharmaceutical Society Name:", [""] + available_societies)

# Step 2: Add selected society to the report with a delay
if society_name and society_name not in st.session_state.selected_societies:
    st.session_state.selected_societies.append(society_name)

    # Simulate data fetching delay
    with st.spinner("Fetching the data..."):
        time.sleep(3)  # Add a 3-second delay

    # Add static data for the selected society
    new_entry = {"Society Name": society_name, **static_answers[society_name]}
    st.session_state.report_data = pd.concat([st.session_state.report_data, pd.DataFrame([new_entry])], ignore_index=True)

# Step 3: Display the report
if not st.session_state.report_data.empty:
    st.write("Consolidated Tabular Report:")
    st.dataframe(st.session_state.report_data)

    # Provide download option
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Consolidated Report")
        return output.getvalue()

    excel_data = to_excel(st.session_state.report_data)
    st.download_button(
        label="Download Consolidated Report",
        data=excel_data,
        file_name="Consolidated_Pharma_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def send_email(smtp_server, smtp_port, sender_email, sender_password, receiver_email, subject, html_content):
    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    # Choose whether to use SSL or TLS
    try:
        if smtp_port == 465:  # Use SSL
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        elif smtp_port == 587:  # Use TLS
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(sender_email, sender_password)
                server.send_message(msg)
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {e}"

# HTML Table Conversion (for email body)
def dataframe_to_html(df):
    return df.to_html(index=False, border=1, classes="dataframe", justify="center")

# Email Sending Interface
if not st.session_state.report_data.empty:
    # st.write("📧 Email Report:")

    # Collect email details from user input
    receiver_email = "rajpua1@gene.com"
    email_subject = "Consolidated Pharma Society Report"

    # Set Gmail SMTP server settings
    smtp_server = "smtp.gmail.com"  # Gmail SMTP server
    smtp_port = 587  # Choose SSL or TLS

    # Set your sender email here (e.g., your Gmail)
    sender_email = "johnwickcrayons@gmail.com"
    sender_password = "afpt eoyt asaq qzjh"

    # Send email if button clicked
    if st.button("Send data to Google Sheets"):
        if receiver_email and email_subject and sender_email and sender_password:
            html_table = dataframe_to_html(st.session_state.report_data)
            email_body = f"""
            <html>
            <head>
                <style>
                    .dataframe {{
                        font-family: Arial, sans-serif;
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    .dataframe td, .dataframe th {{
                        border: 1px solid #ddd;
                        padding: 8px;
                    }}
                    .dataframe tr:nth-child(even) {{
                        background-color: #f2f2f2;
                    }}
                    .dataframe th {{
                        padding-top: 12px;
                        padding-bottom: 12px;
                        text-align: left;
                        background-color: #4CAF50;
                        color: white;
                    }}
                </style>
            </head>
            <body>
                <p>Dear Recipient,</p>
                <p>Find the attached consolidated report below:</p>
                {html_table}
                <p>Best regards,<br>Pharma Society Insights Team</p>
            </body>
            </html>
            """
            status = send_email(smtp_server, smtp_port, sender_email, sender_password, receiver_email, email_subject, email_body)

            # Display success or error message
            if "successfully" in status:
                st.success("Successfully sent data to Google Sheets!")
            else:
                st.error("Error while appending data to Google Sheets!")

# Chatbot 2.0 Section with Enhanced Styling and Animations
st.markdown('<div class="main-header">🤖 Chatbot 2.0 - Fine-Tuned on Report Data</div>', unsafe_allow_html=True)
st.markdown("📋 This chatbot uses OpenAI and the **consolidated report** data to answer your queries.")

# Custom CSS for chatbot styling and animations
st.markdown("""
    <style>
        .chat-container {
            border: 2px solid #007bff;
            border-radius: 10px;
            padding: 15px;
            background-color: #f8f9fa;
            margin-bottom: 20px;
        }
        .chat-container h3 {
            color: #007bff;
            margin-bottom: 10px;
        }
        .user-message, .assistant-message {
            display: flex;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        .user-message {
            animation: slideInRight 0.5s;
        }
        .assistant-message {
            animation: slideInLeft 0.5s;
        }
        .chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
            background-size: cover;
        }
        .user-avatar {
            background-image: url('https://via.placeholder.com/40/007bff/ffffff?text=U');
        }
        .assistant-avatar {
            background-image: url('https://via.placeholder.com/40/28a745/ffffff?text=A');
        }
        .chat-bubble {
            max-width: 75%;
            padding: 10px 15px;
            border-radius: 15px;
            font-size: 0.95rem;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .user-message .chat-bubble {
            background-color: #007bff;
            color: white;
            border-top-left-radius: 0;
        }
        .assistant-message .chat-bubble {
            background-color: #e9ecef;
            color: #212529;
            border-top-right-radius: 0;
        }
        .fadeIn {
            animation: fadeIn 0.8s ease-in-out;
        }
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideInLeft {
            from { transform: translateX(-100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for Chatbot 2.0 messages
if "messages_2" not in st.session_state:
    st.session_state["messages_2"] = [
        {"role": "assistant", "content": "I am here to answer questions based on your consolidated report. How can I help you?"}
    ]

# Chatbot 2.0 input box
chat_input_2 = st.chat_input("Ask a question about the consolidated report...")

# Format the report data as a context for OpenAI
def format_report_for_context(df):
    if df.empty:
        return "No report data is currently available."
    context = "Here is the consolidated report data:\n"
    for _, row in df.iterrows():
        context += f"Society Name: {row['Society Name']}\n"
        for col in df.columns[1:]:  # Skip 'Society Name'
            context += f"  {col}: {row[col]}\n"
        context += "\n"
    return context.strip()

# Generate a response from OpenAI based on the report and user query
def generate_openai_response(query, report_context):
    try:
        # Construct a dynamic prompt
        prompt = f"""
         You are an AI assistant fine-tuned to answer questions based on a pharmaceutical society consolidated report. 
         Use the following report data to answer user queries accurately if the information exists in the report.
         If the query cannot be answered using the report, respond using your general knowledge i.e. using chat-gpt model:
        
        {report_context}
        
        User's question: {query}
        
        Respond concisely using the data provided.
        """
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            #   model="gpt-4",
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0]["message"]["content"].strip()
    except Exception as e:
        return f"Error generating response: {e}"

# Predefined Prompt Buttons in a grid
st.markdown('<div class="prompt-buttons">', unsafe_allow_html=True)
cols = st.columns(3)

with cols[0]:
    if st.button("List down all the societies inside the Report."):
        chat_input_2 = "List down all the societies inside the Report only if there is report data."
with cols[1]:
    if st.button("Which Society do you think is the best out of all and why?"):
        chat_input_2 = "Which Society do you think is the best out of all and why only if there is report data?"
with cols[2]:
    if st.button("Tell me the society names with highest and lowest count of membership."):
        chat_input_2 = "Tell me the society names with highest and lowest count of membership only if there is report data."
st.markdown('</div>', unsafe_allow_html=True)

# Process Chatbot 2.0 input
if chat_input_2:
    st.session_state["messages_2"].append({"role": "user", "content": chat_input_2})

    # Prepare report data as context
    report_context = format_report_for_context(st.session_state.report_data)

    # Generate a response using OpenAI
    with st.spinner("Generating response..."):
        bot_reply_2 = generate_openai_response(chat_input_2, report_context)

    st.session_state["messages_2"].append({"role": "assistant", "content": bot_reply_2})

# Display Chatbot 2.0 conversation with new styling
for msg in st.session_state["messages_2"]:
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div class="user-message">
                <div class="chat-avatar user-avatar"></div>
                <div class="chat-bubble">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True
        )
    elif msg["role"] == "assistant":
        st.markdown(
            f"""
            <div class="assistant-message">
                <div class="chat-avatar assistant-avatar"></div>
                <div class="chat-bubble">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True
        )
st.markdown('</div>', unsafe_allow_html=True)

# Header section
st.markdown('<div class="main-header">💬 Pharma Insights Chatbot </div>', unsafe_allow_html=True)
st.markdown('💡 This app features a chatbot powered by OpenAI for answering society-related queries.', unsafe_allow_html=True)

# Predefined Prompt Buttons in a grid
st.markdown('<div class="prompt-buttons">', unsafe_allow_html=True)
cols = st.columns(3)

prompt = None

with cols[0]:
    if st.button("What are the top 10 oncology societies in California actively supporting clinical trials and research initiatives?"):
        prompt = "What are the top 10 oncology societies in California actively supporting clinical trials and research initiatives?"
with cols[1]:
    if st.button("Which Oncology Society in the World has the largest membership network and reach?"):
        prompt = "Which Oncology Society in the World has the largest membership network and reach?"
with cols[2]:
    if st.button("Which Oncology Societies in California collaborate with pharmaceutical companies for drug development initiatives?"):
        prompt = "Which Oncology Societies in California collaborate with pharmaceutical companies for drug development initiatives?"

# Add additional buttons in another row
cols = st.columns(3)
with cols[0]:
    if st.button("List the Oncology Societies in California that offer leadership opportunities for healthcare professionals."):
        prompt = "List the Oncology Societies in California that offer leadership opportunities for healthcare professionals."
with cols[1]:
    if st.button("Which Oncology Societies in California are most active in influencing state healthcare policies?"):
        prompt = "Which Oncology Societies in California are most active in influencing state healthcare policies?"
with cols[2]:
    if st.button("Identify oncology societies in California that provide resources or support for community-based oncology practices."):
        prompt = "Identify oncology societies in California that provide resources or support for community-based oncology practices."
st.markdown('</div>', unsafe_allow_html=True)

# Chat Input Section
user_input = st.chat_input("Ask a question or select a prompt...")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I assist you today?"}]

# Append user input or prompt to chat history
if prompt or user_input:
    user_message = prompt if prompt else user_input
    st.session_state["messages"].append({"role": "user", "content": user_message})

    # Query OpenAI API with the current messages
    with st.spinner("Generating response..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=st.session_state["messages"]
            )
            bot_reply = response.choices[0]["message"]["content"]
            st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        except Exception as e:
            bot_reply = f"Error retrieving response: {e}"
            st.session_state["messages"].append({"role": "assistant", "content": bot_reply})

# Display chat history sequentially
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])