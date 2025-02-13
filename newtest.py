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
    "PSOH (Pennsylvania Society of Oncology and Hematology)": {
        "Membership Count": 10000,
        "Community Sites": "Yes, PSOH does encompass community sites. Community sites are an important part of cancer care and treatment.",
        "Influential on Policy": "No, PSOH is primarily focused on education, research, and advocacy at the national level, not state or local policy.",
        "Engagement with Leadership": "Yes, The PSOH provides engagement opportunities with leadership through various events and programs.",
        "Clinical Trial Recruitment": "Yes, PSOH does provide support for clinical trial recruitment, as they often collaborate with researchers and institutions to help connect patients with appropriate clinical trials.",
        "Engagement with Payors": "No, PSOH does not provide engagement opportunity with payors. PSOH is primarily a professional society for oncologists and hematologists, focused on education, research, and collaboration within the field, rather than facilitating interactions with payors.",
        "Area Experts on Board": "Yes,  The board of PSOH likely includes area experts in the fields of oncology and hematology to guide and support the organization's mission.",
        "Therapeutic Research Collaborations": "No, PSOH is primarily a professional organization focused on education and advocacy for oncologists and hematologists, not therapeutic research collaborations.",
        "Top Experts on Board": "Yes, the board of PSOH includes top therapeutic area experts. Members of PSOH's board are leaders in the field of oncology and hematology, bringing their expertise to guide the organization.",
        "Region": "Pennsylvania"
    },
    "WVOS (West Virginia Oncology Society)": {
        "Membership Count": 187,
        "Community Sites": "No, WVOS does not encompass community sites, as it specifically focuses on oncology services within West Virginia.",
        "Influential on Policy": "No, There is no evidence of WVOS influencing state or local policy.",
        "Engagement with Leadership": "No, WVOS does not provide engagement opportunity with leadership. WVOS focuses primarily on education and support for oncology professionals rather than leadership development.",
        "Clinical Trial Recruitment": "No, WVOS does not provide support for clinical trial recruitment. WVOS is primarily focused on education and advocacy for oncology professionals in West Virginia.",
        "Engagement with Payors": "No, WVOS does not provide engagement opportunity with payors. WVOS is a professional organization for oncology professionals and focuses on education, advocacy, and networking within the field of oncology.",
        "Area Experts on Board": "No, The West Virginia Oncology Society does not include area experts on its board. The organization primarily consists of healthcare professionals who specialize in treating cancer rather than non-medical experts.",
        "Therapeutic Research Collaborations": "No, lack of information.",
        "Top Experts on Board": "Yes, the WVOS includes top therapeutic area experts on its board. The WVOS board members are oncology specialists who bring expertise and knowledge in the field of cancer treatment.",
        "Region": "Virginia"
    },
    "DSCO (Delaware Society of Clinical Oncology)": {
        "Membership Count": 1104,
        "Community Sites": "Yes, DSCO encompasses community sites because they are part of the oncology network in Delaware.",
        "Influential on Policy": "No, DSCO is more focused on providing education and networking opportunities for oncology professionals rather than lobbying for policy change.",
        "Engagement with Leadership": "No, DSCO does not provide direct engagement opportunities with its leadership, as it is focused on providing clinical oncology services and support to its members.",
        "Clinical Trial Recruitment": "No, DSCO does not provide support for clinical trial recruitment.",
        "Engagement with Payors": "No, DSCO does not provide engagement opportunities with payors. The primary focus of DSCO is on clinical oncology practices and the advancement of cancer care rather than engaging with payors.",
        "Area Experts on Board": "Yes, the organization's board likely includes area experts in the field of clinical oncology to ensure expertise and guidance in decision-making.",
        "Therapeutic Research Collaborations": "No, DSCO focuses primarily on education and advocacy for clinical oncology professionals in Delaware.",
        "Top Experts on Board": "No, the DSCO may not include top therapeutic area experts on its board. Justification: There is no specific information available to confirm the presence of top therapeutic area experts on the board of DSCO.",
        "Region": "Delaware"
    },
    "OSNJ (Oncology Society of New Jersey)": {
        "Membership Count": 1649,
        "Community Sites": "Yes, OSNJ encompasses community sites. Community sites are an integral part of providing comprehensive cancer care to patients throughout the state.",
        "Influential on Policy": "No, OSNJ is primarily focused on providing education and resources for oncology professionals in New Jersey, rather than influencing state or local policy.",
        "Engagement with Leadership": "Yes, OSNJ provides engagement opportunities with leadership through networking events, conferences, and committees.",
        "Clinical Trial Recruitment": "Yes, OSNJ provides support for clinical trial recruitment. OSNJ offers resources and assistance to help connect patients with ongoing clinical trials.",
        "Engagement with Payors": "Yes, OSNJ likely provides engagement opportunities with payors as payor engagement is crucial for navigating the healthcare landscape and ensuring optimal care for patients.",
        "Area Experts on Board": "Yes, OSNJ includes area experts on its board to ensure that the organization benefits from a wide range of expertise and perspectives related to oncology in New Jersey.",
        "Therapeutic Research Collaborations": "Yes, OSNJ is involved in therapeutic research collaborations. OSNJ frequently collaborates with pharmaceutical companies, academic institutions, research organizations, and other medical societies to conduct clinical trials and research studies aimed at advancing cancer treatment and care.",
        "Top Experts on Board": "Yes, OSNJ includes top therapeutic area experts on its board. The organization is dedicated to promoting excellence in oncology practice and research, so it is likely that top experts in the field would be part of the board.",
        "Region": "New Jersey"
    },
    "ESHOS (Empire State Hematology Oncology Society)": {
        "Membership Count": 1200,
        "Community Sites": "Yes, ESHOS encompasses community sites as it aims to promote hematology and oncology education, research, and care across the state of New York, including community-based practices.",
        "Influential on Policy": "No, ESHOS does not have a direct influence on state or local policy as it is a medical society focused on hematology and oncology, not policy advocacy.",
        "Engagement with Leadership": "Yes, ESHOS provides engagement opportunities with leadership. This can be seen through various initiatives such as leadership forums, mentorship programs, and networking events that allow members to interact with and learn from established leaders in the field of hematology and oncology.",
        "Clinical Trial Recruitment": "No, ESHOS does not provide support for clinical trial recruitment. ESHOS focuses on education and networking opportunities for hematologists and oncologists, rather than facilitating clinical trial recruitment.",
        "Engagement with Payors": "No, ESHOS does not provide engagement opportunities with payors. ESHOS focuses on education and support for hematology and oncology professionals, not collaboration with payors.",
        "Area Experts on Board": "Yes, the board of ESHOS includes area experts in the field of hematology and oncology, providing a diverse range of perspectives and knowledge.",
        "Therapeutic Research Collaborations": "No, ESHOS is primarily a professional organization focused on education and networking for hematology and oncology practitioners, rather than directly involved in therapeutic research collaborations.",
        "Top Experts on Board": "No, ESHOS does not include top therapeutic area experts on its board. As ESHOS is focused on hematology and oncology, it is likely that the board consists of experts in those specific fields rather than across all therapeutic areas.",
        "Region": "New York"
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
    receiver_email = "chouran1@gene.com"
    email_subject = "Consolidated Pharma Society Report Old"

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
