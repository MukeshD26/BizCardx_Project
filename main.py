import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import mysql.connector as sql
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re

icon = Image.open("page_icon.png")
st.set_page_config(page_title="OCR the business card image and extracting the data | By MK",
                   page_icon=icon,
                   layout="centered",
                   initial_sidebar_state="collapsed",
                   menu_items={'About': """# This app is created by *!Mukesh!*"""})
st.markdown("<h1 style='text-align: center; color: purple;'>OCR Business Card Data</h1>", unsafe_allow_html=True)


def setting_bg():
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(to bottom right, #03FBFF, #DAF7A6);
            background-size: cover;
            transition: all 0.5s ease;
            }}
    </style>""", unsafe_allow_html=True)


setting_bg()

selected = option_menu(None, ["Home", "OCR Data", "Modify Data"],
                       icons=["house-door-fill", "database-fill-up", "pen-fill"],
                       default_index=0,
                       orientation="",
                       styles={"nav-link": {"font-size": "25px", "text-align": "centre", "margin": "0px",
                                            "--hover-color": "#05FAD5",
                                            "transition": "color 0.5s ease, background-color 0.5s ease"},
                               "icon": {"font-size": "35px"},
                               "container": {"max-width": "6000px", "padding": "10px", "border-radius": "5px"},
                               "nav-link-selected": {"background-color": "#055EFA", "color": "purple"}})

reader = easyocr.Reader(['en'])

db = sql.connect(host="localhost",
                 user="root",
                 password="Mac@2698",
                 database="BizCardx"
                 )
mycursor = db.cursor(buffered=True)

#mycursor.execute("create database BizCardx")

mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''')

if selected == "Home":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## :red[**Project Name :**] OCR the BizCardx")
        st.markdown("## :red[**Python Libraries :**] Streamlit, Pandas, Mysql and easy OCR")
        st.markdown(
            "## :red[**Overview :**] The Business Card Data Extraction Web Application, built with easyOCR and Streamlit, revolutionizes contact management. Users can upload business card images, extract accurate details using easyOCR, and edit or delete information as needed. It ensures time-efficient, error-free digitalization of business cards, empowering users to effortlessly manage and verify their contacts, thereby enhancing networking effectiveness and communication.")
    with col2:
        st.image("home.png")

if selected == "OCR Data":
    st.markdown("### Upload a Business Card")
    if not os.path.exists("uploaded_cards"):
        os.makedirs("uploaded_cards")

    uploaded_card = st.file_uploader("upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])

    if uploaded_card is not None:
        # Save the uploaded image to the uploaded_cards directory
        uploaded_file_path = os.path.join("uploaded_cards", uploaded_card.name)
        with open(uploaded_file_path, "wb") as f:
            f.write(uploaded_card.getbuffer())

        st.success(f"Image '{uploaded_card.name}' uploaded successfully.")


        def image_preview(image, res):
            for (bbox, text, prob) in res:
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15, 15)
            plt.axis('off')
            plt.imshow(image)


        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("### You have uploaded the card")
            st.image(uploaded_card)

        with col2:
            st.markdown("#     ")
            with st.spinner("Please wait image processing..."):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### Image Processed and Data Extracted")
                st.pyplot(image_preview(image, res))

        saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
        result = reader.readtext(saved_img, detail=0, paragraph=False)


        def img_to_binary(file):

            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData


        data = {"company_name": [],
                "card_holder": [],
                "designation": [],
                "mobile_number": [],
                "email": [],
                "website": [],
                "area": [],
                "city": [],
                "state": [],
                "pin_code": [],
                "image": img_to_binary(saved_img)
                }


        def get_data(res):
            for ind, i in enumerate(res):

                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] + "." + res[5]


                elif "@" in i:
                    data["email"].append(i)


                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])


                elif ind == len(res) - 1:
                    data["company_name"].append(i)


                elif ind == 0:
                    data["card_holder"].append(i)


                elif ind == 1:
                    data["designation"].append(i)

                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)

                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)

                if len(i) >= 6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pin_code"].append(i[10:])


        get_data(result)


        def create_df(data):
            df = pd.DataFrame(data)
            return df


        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)

        if st.button("Upload to Database"):
            for i, row in df.iterrows():
                sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                mycursor.execute(sql, tuple(row))

                db.commit()
            st.success("#### Uploaded to database successfully!")

if selected == "Modify Data":
    col1, col2, col3 = st.columns([3, 3, 2])
    col2.markdown("## Alter or Delete the data here")
    column1, column2 = st.columns(2, gap="large")
    try:
        with column1:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            mycursor.execute(
                "select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                (selected_card,))
            result = mycursor.fetchone()

            company_name = st.text_input("Company_Name", result[0])
            card_holder = st.text_input("Card_Holder", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile_Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin_Code", result[9])

            if st.button("Commit changes to DB"):
                mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (
                company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code,
                selected_card))
                db.commit()
                st.success("Information updated in database successfully.")

        with column2:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                db.commit()
                st.success("Business card information deleted from database.")
    except:
        st.warning("There is no data available in the database")

    if st.button("View updated data"):
        mycursor.execute(
            "select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
        updated_df = pd.DataFrame(mycursor.fetchall(),
                                  columns=["Company_Name", "Card_Holder", "Designation", "Mobile_Number", "Email",
                                           "Website", "Area", "City", "State", "Pin_Code"])
        st.write(updated_df)
