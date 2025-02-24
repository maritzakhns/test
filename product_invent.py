import streamlit as st
import os
import pandas as pd
from datetime import datetime
from PIL import Image

# Inisialisasi DataFrames
stocklist = pd.read_csv('toko_bangunan.csv')
transaction = pd.read_csv('new_transaksitoko.csv')
rfid_scan = pd.read_csv('rfid_user.csv', dtype={'rfid_id': str})

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Inventory Management", 
    page_icon="📦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Mengubah warna primary button */
    .stButton > button[data-baseweb="button"] {
        background-color: #00838F;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
    }
    
    /* Hover effect untuk button */
    .stButton > button[data-baseweb="button"]:hover {
        background-color: #006064;
    }
    
    /* Mengubah warna secondary button */
    .stButton > button[kind="secondary"] {
        background-color: #78909C;
        border: none;
    }
    
    /* Mengubah warna sidebar */
    .css-1d391kg {
        background-color: #E0F7FA;
    }
    
    /* Mengubah style header */
    .stTitle {
        color: #00838F;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    /* Mengubah style tabel */
    .stDataFrame {
        border: 1px solid #B2EBF2;
        border-radius: 8px;
    }
    
    /* Mengubah warna text input */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border-color: #B2EBF2;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi session state
if 'rfid_input' not in st.session_state:
    st.session_state.rfid_input = ''
if 'selected_item' not in st.session_state:
    st.session_state.selected_item = None
if 'item_name' not in st.session_state:
    st.session_state.item_name = None
if 'qty' not in st.session_state:
    st.session_state.qty = None
if 'purpose' not in st.session_state:
    st.session_state.purpose = None
if 'waiting_for_scan' not in st.session_state:
    st.session_state.waiting_for_scan = False
if 'person_in_charge' not in st.session_state:
    st.session_state.person_in_charge = None
if 'transaction' not in st.session_state:
    st.session_state.transaction = transaction
if 'pending_transaction_index' not in st.session_state:
    st.session_state.pending_transaction_index = None
if 'scan_result' not in st.session_state:
    st.session_state.scan_result = None
if 'input_value' not in st.session_state:
    st.session_state.input_value = ""
if 'page' not in st.session_state:
    st.session_state.page = "Main Page"
if 'transaction_type' not in st.session_state:
    st.session_state.transaction_type = None
if 'dialog_active' not in st.session_state:
    st.session_state.dialog_active = False
if 'scan' not in st.session_state:
    st.session_state.scan = False
if 'confirm' not in st.session_state:
    st.session_state.confirm = False

# Sidebar navigasi
st.sidebar.title("Inventory Management")
page = st.sidebar.selectbox("Pages", 
    ["Main Page", "Register New Product", "Transaction History", "Monthly Report"]
)

if page == "Main Page":
    # Dialog Konfirmasi Transaksi
    @st.dialog("Confirm Transaction")
    def confirm():
        st.session_state.dialog_active = True
        if st.session_state.pending_transaction_index is not None:
            transaction_data = st.session_state.transaction.iloc[st.session_state.pending_transaction_index]
            
            st.markdown("### Transaction Details")
            st.write(f"**Item No:** {transaction_data['item no']}")
            st.write(f"**Selected Item:** {transaction_data['item name']}")
            st.write(f"**Status:** {transaction_data['status'].upper()}")
            st.write(f"**Quantity Input:** {transaction_data['qty input']}")
            st.write(f"**Quantity Output:** {transaction_data['qty output']}")
            st.write(f"**Purpose:** {transaction_data['purpose']}")

            if st.session_state.get('scan_result'):
                st.info(f"**Person in Charge:** {st.session_state.scan_result['id_name']}")
            else:
                st.warning("ID Card Not Scanned Yet")

            button_col1, button_col2 = st.columns(2)

            with button_col1:
                if st.button("Cancel", key="cancel_transaction_confirm", type="secondary"):
                    st.session_state.scan_result = None
                    st.session_state.input_value = ""
                    st.session_state.waiting_for_scan = False
                    st.session_state.page = "Scan ID Card" 
                    st.rerun()

            with button_col2:
                if st.session_state.get('scan_result'):
                    if st.button("Confirm Transaction", key="confirm_transaction_dialog"):
                        idx = st.session_state.pending_transaction_index
                        id_name = st.session_state.scan_result['id_name']
                        st.session_state.transaction.at[idx, 'person in charge'] = id_name

                        item_no = st.session_state.transaction.at[idx, 'item no']
                        status = st.session_state.transaction.at[idx, 'status']
                        qty_input = st.session_state.transaction.at[idx, 'qty input']
                        qty_output = st.session_state.transaction.at[idx, 'qty output']

                        if qty_input == "0":
                            qty = st.session_state.transaction.at[idx, 'qty output']
                        elif qty_output == "0":
                            qty = st.session_state.transaction.at[idx, 'qty input']

                        if status == "out":
                            stocklist.loc[stocklist['item no'] == item_no, 'quantity'] -= qty
                        elif status == "in":
                            stocklist.loc[stocklist['item no'] == item_no, 'quantity'] += qty

                        stocklist.to_csv('toko_bangunan.csv', index=False)
                        st.session_state.transaction.to_csv('new_transaksitoko.csv', index=False)
                        st.session_state.person_in_charge = id_name
                        st.session_state.page = "Main Page"
                        st.session_state.pending_transaction_index = None
                        st.session_state.scan_result = None
                        st.session_state.waiting_for_scan = False
                     
                        st.rerun()

    # Dialog Scan ID Card
    @st.dialog("Scan ID Card")
    def scan():
        st.session_state.dialog_active = True
        st.info("Please place your ID card near the scanner")
        
        id_code = st.text_input("Scan RFID Card", key='rfid_input', 
                                label_visibility="collapsed", value=st.session_state.input_value)
            
        # Jika ada input ID dan belum ada scan result
        if id_code and st.session_state.scan_result is None:
            st.session_state.input_value = id_code
            
            # Format ID dengan leading zeros
            id_code = str(id_code).zfill(10)
            
            # Cek ID di database
            matched_user = rfid_scan[rfid_scan['rfid_id'] == id_code]
            
            if not matched_user.empty:
                # Tampilkan nama user
                id_name = matched_user['nama'].iloc[0]
                
                # Simpan hasil scan di session state
                st.session_state.scan_result = {
                    'id_code': id_code,
                    'id_name': id_name
                }
                st.success(f"ID Verified: **{id_name}**")
                st.session_state.page = "Confirm Transaction"
                st.rerun()
                
            else:
                st.error("Card not registered!")

    # Routing dialog
    if st.session_state.page == "Scan ID Card":
        st.session_state.scan = True 
        scan()
    elif st.session_state.page == "Confirm Transaction":
        st.session_state.confirm = True 
        confirm()

    if st.session_state.dialog_active and not (st.session_state.get('scan') or st.session_state.get('confirm')):
        st.session_state.scan_result = None
        st.session_state.input_value = ""
        st.session_state.waiting_for_scan = False
        st.session_state.page = "Main Page"
        
    st.title('Product Stocks')
    search = st.text_input("", value=None, placeholder="Search product here")
    # Filter berdasarkan pencarian
    if search:
        filtered_stocklist = stocklist[stocklist['item name'].str.contains(search, case=False, na=False)]
        empty_rows = pd.DataFrame([[""] * len(stocklist.columns)] * 8, columns=stocklist.columns)
        final_display = pd.concat([filtered_stocklist, empty_rows], ignore_index=True)
    else:
        final_display = stocklist

    st.dataframe(final_display, use_container_width=True, height=350)

# Tombol untuk mengambil produk
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        if st.button("Take Product", use_container_width=True, icon="⏫", type="primary"):
            @st.dialog('Take Out Product')
            def takeout_product():
                st.session_state.transaction_type = "takeout"
                scanned_item = st.text_input("Scan Item Number:", value=None)
                if scanned_item:
                # Cek apakah item number ada di stocklist
                    if scanned_item in stocklist['item no'].values:
                       item_name = stocklist.loc[stocklist['item no'] == scanned_item, 'item name'].values[0]
                       st.session_state.item_name = item_name
                       st.text(f'Selected Item: \n {item_name}')

                # Check if image exists in images folder
                       image_path = os.path.join("item_images", f"{scanned_item}.jpg")
                       if os.path.exists(image_path):
                         st.image(image_path, width=100)
                       else:
                        st.warning("No image found for this item")

                       qty = st.number_input("Enter Quantity:", min_value=1, step=1)
                       st.session_state.qty = qty

                       purpose = st.selectbox("Select Purpose:", ['-', 'Maintenance', 'Construction', 'Renovation'])
                       st.session_state.purpose = purpose

                       button_col1, button_col2 = st.columns(2, gap="medium")
                       with button_col1:
                        if st.button("Cancel", key="cancel_dialog_take", type="secondary"):
                            st.rerun()
                       with button_col2:
                        if st.button("Confirm", key="confirm_dialog_take", type="primary"):
                            st.session_state.selected_item = scanned_item
                            status = "out"
                            qty_input = "0"
                            current_date = datetime.today().strftime('%Y-%m-%d')
                            new_data = pd.DataFrame({
                                'date': [current_date],
                                'item no': [scanned_item],
                                'item name': [item_name],
                                'purpose': [purpose],
                                'status': [status],
                                'qty input': [qty_input], 
                                'qty output': [qty], 
                                'person in charge': [None]
                            })
                            st.session_state.transaction = pd.concat([st.session_state.transaction, new_data], ignore_index=True)
                            st.session_state.pending_transaction_index = len(st.session_state.transaction) - 1
                            st.session_state.waiting_for_scan = True
                            st.session_state.page = "Scan ID Card"
                            st.rerun()
                    else:
                        st.error("Item number not found in stock list")

            takeout_product()
        
        if st.session_state.waiting_for_scan:
            scan()


    with col2:
        if st.button("Add Product", use_container_width=True, icon="⏬", type="primary"):
            @st.dialog('Add Product')
            def add_product():   
                st.session_state.transaction_type = "add"
                scanned_item = st.text_input("Scan Item Number:", value=None)
                if scanned_item:
                # Cek apakah item number ada di stocklist
                    if scanned_item in stocklist['item no'].values:
                        item_name = stocklist.loc[stocklist['item no'] == scanned_item, 'item name'].values[0]
                        st.session_state.item_name = item_name
                        st.text(f"Selected Item: \n {item_name}")
                    
                        # Check if image exists in images folder
                        image_path = os.path.join("item_images", f"{scanned_item}.jpg")
                        if os.path.exists(image_path):
                            st.image(image_path, width=100)
                        else:
                            st.warning("No image found for this item")

                        qty = st.number_input("Enter Quantity:", min_value=1, step=1)
                        st.session_state.qty = qty
                        
                        purpose = st.selectbox("Select Purpose:", ['-', 'Maintenance', 'Construction', 'Renovation'])
                        st.session_state.purpose = purpose
                        
                        button_col1, button_col2 = st.columns(2)
                        with button_col1:
                            if st.button("Cancel", key="cancel_dialog_add", type="secondary"):
                                st.rerun()
                        with button_col2:
                            if st.button("Confirm", key="confirm_dialog_add", type="primary"):
                                st.session_state.selected_item = scanned_item
                                status = "in"
                                qty_output = "0"
                                current_date = datetime.today().strftime('%Y-%m-%d')
                                new_data = pd.DataFrame({
                                    'date': [current_date],
                                    'item no': [scanned_item],
                                    'item name': [item_name],  
                                    'purpose': [purpose],
                                    'status': [status],
                                    'qty input': [qty],
                                    'qty output' : [qty_output],
                                    'person in charge': [None]
                                })
                                
                                st.session_state.transaction = pd.concat([st.session_state.transaction, new_data], ignore_index=True)
                                st.session_state.pending_transaction_index = len(st.session_state.transaction) - 1
                                st.session_state.waiting_for_scan = True
                                st.session_state.page = "Scan ID Card"
                                st.rerun()
                    else:
                        st.error("Item number not found in stock list")

            add_product()

    if st.session_state.waiting_for_scan:
        scan()

    if not os.path.exists('item_images'):
        os.makedirs('item_images')

    def save_uploaded_image(uploaded_file, item_number):
        try:
            # Buka gambar menggunakan PIL
            image = Image.open(uploaded_file)
            
            # Convert ke RGB jika dalam mode RGBA
            if image.mode == 'RGBA':
                image = image.convert('RGB')
                
            # Resize gambar jika terlalu besar (opsional)
            max_size = (800, 800)  # Maximum dimensions
            image.thumbnail(max_size, Image.LANCZOS)
            
            # Simpan gambar
            save_path = os.path.join("item_images", f"{item_number}.jpg")
            image.save(save_path, "JPEG", quality=85)
            return True, "Image saved successfully"
        except Exception as e:
            return False, str(e)
            
# Halaman lainnya tetap sama seperti sebelumnya
if page == "Register New Product":
    @st.dialog("Confirm Transaction")
    def confirm():
        st.session_state.dialog_active = True 
        if st.session_state.pending_transaction_index is not None:
            transaction_data = st.session_state.transaction.iloc[st.session_state.pending_transaction_index]
            
            st.markdown("### Transaction Details")
            st.write(f"**Item No:** {transaction_data['item no']}")
            st.write(f"**Selected Item:** {transaction_data['item name']}")
            st.write(f"**Status:** {transaction_data['status'].upper()}")
            st.write(f"**Quantity Input:** {transaction_data['qty input']}")
            st.write(f"**Quantity Output:** {transaction_data['qty output']}")
            st.write(f"**Purpose:** {transaction_data['purpose']}")

            if st.session_state.get('scan_result'):
                st.info(f"**Person in Charge:** {st.session_state.scan_result['id_name']}")
            else:
                st.warning("ID Card Not Scanned Yet")

            button_col1, button_col2 = st.columns(2)

            with button_col1:
                if st.button("Cancel Transaction", key="cancel_transaction_confirm", type="secondary"):
                    st.session_state.scan_result = None
                    st.session_state.input_value = ""
                    st.session_state.waiting_for_scan = False
                    st.session_state.page = "Scan ID Card" 
                    st.rerun()

            with button_col2:
                if st.session_state.get('scan_result'):
                    if st.button("Confirm Transaction", key="confirm_transaction_dialog", type="primary"):
                        idx = st.session_state.pending_transaction_index
                        id_name = st.session_state.scan_result['id_name']
                        st.session_state.transaction.at[idx, 'person in charge'] = id_name

                        item_no = st.session_state.transaction.at[idx, 'item no']
                        status = st.session_state.transaction.at[idx, 'status']
                        qty_input = st.session_state.transaction.at[idx, 'qty input']
                        qty_output = st.session_state.transaction.at[idx, 'qty output']

                        if qty_input == "0":
                            qty = st.session_state.transaction.at[idx, 'qty output']
                        elif qty_output == "0":
                            qty = st.session_state.transaction.at[idx, 'qty input']

                        if status == "out":
                            stocklist.loc[stocklist['item no'] == item_no, 'quantity'] -= qty
                        elif status == "in":
                            stocklist.loc[stocklist['item no'] == item_no, 'quantity'] += qty

                        stocklist.to_csv('toko_bangunan.csv', index=False)
                        st.session_state.transaction.to_csv('new_transaksitoko.csv', index=False)

                        st.session_state.pending_transaction_index = None
                        st.session_state.scan_result = None
                        st.session_state.waiting_for_scan = False
                        st.session_state.person_in_charge = id_name
                        st.session_state.page = "Register New Product"
                        st.rerun()
                else:
                    st.button("Confirm Transaction", key="confirm_transaction_disabled", type="primary", disabled=True)
        else:
            st.warning("No pending transaction found.")
            if st.button("Back to Regsiter New Product", key="back_to_regis_confirm"):
                st.session_state.page = "Register New Product"
                st.rerun()

    # Dialog Scan ID Card
    @st.dialog("Scan ID Card")
    def scan():
        st.session_state.dialog_active = True 
        st.info("Please place your ID card near the scanner")
        
        id_code = st.text_input("Scan RFID Card", key='rfid_input', 
                                label_visibility="collapsed", value=st.session_state.input_value)
        
        cancel_button = st.button("Cancel", key="cancel_scan_button")

        if cancel_button:
            st.session_state.scan_result = None
            st.session_state.input_value = ""
            st.session_state.waiting_for_scan = False
            st.session_state.page = "Register New Product"
            st.rerun()
            

        # Jika ada input ID dan belum ada scan result
        if id_code and st.session_state.scan_result is None:
            st.session_state.input_value = id_code
            
            # Format ID dengan leading zeros
            id_code = str(id_code).zfill(10)
            
            # Cek ID di database
            matched_user = rfid_scan[rfid_scan['rfid_id'] == id_code]
            
            if not matched_user.empty:
                # Tampilkan nama user
                id_name = matched_user['nama'].iloc[0]
                
                # Simpan hasil scan di session state
                st.session_state.scan_result = {
                    'id_code': id_code,
                    'id_name': id_name
                }
                st.success(f"ID Verified: **{id_name}**")
                st.session_state.page = "Confirm Transaction"
                st.rerun()
                
            else:
                st.error("Card not registered!")

    # Routing dialog
    if st.session_state.page == "Scan ID Card":
        st.session_state.scan = True 
        scan()
    elif st.session_state.page == "Confirm Transaction":
        st.session_state.confirm = True
        confirm()
    
    if st.session_state.dialog_active and not (st.session_state.get('scan') or st.session_state.get('confirm')):
        st.session_state.scan_result = None
        st.session_state.input_value = ""
        st.session_state.waiting_for_scan = False
        st.session_state.pending_transaction_index = None
        st.session_state.scan_result = None
        st.session_state.dialog_active = False
        st.rerun()
        

    st.title('Register New Product')
    search = st.text_input("", value=None, placeholder="Search product here")
    if search:
        filtered_stocklist = stocklist[stocklist['item name'].str.contains(search, case=False, na=False)]
        empty_rows = pd.DataFrame([[""] * len(stocklist.columns)] * 8, columns=stocklist.columns)
        final_display = pd.concat([filtered_stocklist, empty_rows], ignore_index=True)
    else:
        final_display = stocklist

    st.dataframe(final_display, use_container_width=True, height=350)
    
    if st.button("Add New Product", type="primary"):
        @st.dialog('Add New Product')
        def new_product():
            global stocklist 
            new_item_number = st.text_input("Scan Item Number", value=None)
            
            if new_item_number:
                # Cek apakah item number sudah ada
                if new_item_number in stocklist['item no'].values:
                    st.error("Item number already exists!")
                else:
                    # User input untuk item name dan quantity
                    new_item_name = st.text_input("New Item Name", value=None)
                    new_item_quantity = st.number_input("Initial Quantity", min_value=0, step=1, value=0, placeholder='0')
                    purpose = st.selectbox('Select Purpose:', ['-', 'Maintenance', 'Construction', 'Renovation'])
                    uploaded_file = st.file_uploader("Upload Product Image", type=['png', 'jpg', 'jpeg'])
                    if uploaded_file:
                        st.image(uploaded_file, caption="Preview", width=200)  # Preview gambar
                        
                    button_col1, button_col2 = st.columns(2, gap="medium")
                    with button_col1:
                        if st.button("Cancel", key="cancel_dialog", type="secondary"):
                            st.rerun()
                    
                    with button_col2:
                        if st.button("Confirm", key="confirm_dialog_new", type="primary"):
                            if new_item_name:
                                # Dapatkan nomor urut terakhir
                                last_item_no = stocklist['no'].max() if 'no' in stocklist.columns else 0
                                new_item_num = int(last_item_no) + 1 if not pd.isna(last_item_no) else 1
                                
                                # Tambah data ke stocklist
                                new_stock_data = pd.DataFrame({
                                    'no': [new_item_num],
                                    'item no': [new_item_number],  # Menggunakan hasil scan
                                    'item name': [new_item_name],
                                    'quantity': [0]
                                })
                                
                                stocklist = pd.concat([stocklist, new_stock_data], ignore_index=True)
                                stocklist.to_csv('toko_bangunan.csv', index=False)
                                
                                # Tambah ke tabel transaksi jika quantity > 0
                                if new_item_quantity > 0:
                                    current_date = datetime.today().strftime('%Y-%m-%d')
                                    new_trans_data = pd.DataFrame({
                                        'date': [current_date],
                                        'item no': [new_item_number],
                                        'item name': [new_item_name],
                                        'purpose': [purpose],
                                        'status': ['new'],
                                        'qty input': [new_item_quantity],
                                        'qty output': "0",
                                        'person in charge': [None]
                                    })
                                    
                                    st.session_state.transaction = pd.concat([st.session_state.transaction, new_trans_data], ignore_index=True)
                                    st.session_state.pending_transaction_index = len(st.session_state.transaction) - 1
                                    st.session_state.waiting_for_scan = True
                                    st.session_state.page = "Scan ID Card" 
                                    st.rerun()
                            else:
                                st.error("Please enter item name")

        new_product()

        if st.session_state.waiting_for_scan:
            scan()

elif page == "Transaction History":
    st.title("Transaction History")
    sorted_transaction = st.session_state.transaction.sort_values(by='date', ascending=False)
    st.dataframe(sorted_transaction, use_container_width=True)  

elif page == "Monthly Report":
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1)) # Histori 5 tahun ke belakang
    months = list(range(1, 13))  

    col1, col2 = st.columns(2)

    with col1:
        selected_year = st.selectbox("Select Year", years, index=len(years)-1)  # Default ke tahun sekarang

    with col2:
        selected_month = st.selectbox("Select Month", months, index=datetime.now().month-1)

    def calculate_monthly_report(data, year, month, stocklist):
    # Membuat tanggal awal dan akhir bulan yang dipilih
        start_date = pd.Timestamp(year=year, month=month, day=1)
        end_date = start_date + pd.offsets.MonthEnd(0)
        report = {}
        
        # Konversi kolom date dan qty input ke tipe data yang sesuai
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        data['qty input'] = pd.to_numeric(data['qty input'], errors='coerce')
        
        # Mendapatkan semua item yang memiliki transaksi masuk sebelum atau pada bulan yang dipilih
        items_with_input = data[
            (data['qty input'] > 0) & 
            (data['date'] <= end_date)     
        ].groupby('item no').agg({
            'date': 'min' 
        }).reset_index()
        
        # Loop untuk setiap item yang memiliki transaksi masuk
        for _, item_row in items_with_input.iterrows():
            item_no = item_row['item no']
            try:
                item_data = data[data['item no'] == item_no]

                is_new_item = item_data[
                (item_data['date'] >= start_date) & 
                (item_data['date'] < end_date) & 
                (item_data['status'] == 'new')
                ].any().any()
                
                # Cek transaksi di bulan yang dipilih
                month_transactions = item_data[
                    (item_data['date'] >= start_date) & 
                    (item_data['date'] < end_date)
                ]
                
                # Inisialisasi initial_qty
                initial_qty = 0
                
                # Ambil data sebelum bulan yang dipilih untuk initial qty
                previous_transactions = item_data[item_data['date'] < start_date]

                if is_new_item:
                    initial_qty = 0
                    total_input = month_transactions['qty input'].sum()
                    total_output = pd.to_numeric(month_transactions['qty output'], errors='coerce').sum()
                else:
                    # Untuk barang lama, gunakan logika yang sudah ada
                    previous_transactions = item_data[item_data['date'] < start_date]
                
                if not previous_transactions.empty:
                    # Jika ada transaksi sebelumnya, hitung dari transaksi
                    total_previous_input = previous_transactions['qty input'].sum()
                    total_previous_output = pd.to_numeric(previous_transactions['qty output'], errors='coerce').sum()
                    initial_qty = total_previous_input - total_previous_output
                else:
                    # Jika tidak ada transaksi sebelumnya, cek di stocklist
                    stock_item = stocklist[stocklist['item no'] == item_no]
                    if not stock_item.empty:
                        initial_qty = float(stock_item['quantity'].values[0])
                    else:
                        initial_qty = 0
                
                # Hitung total input dan output bulan ini
                if month_transactions.empty:
                    total_input = 0  
                    total_output = 0
                else:
                    total_input = month_transactions['qty input'].sum()
                    total_output = pd.to_numeric(month_transactions['qty output'], errors='coerce').sum()
                
                end_qty = initial_qty + total_input - total_output
                
                item_name = item_data['item name'].iloc[0]
                
                report[item_no] = {
                    'month': month,
                    'year': year,
                    'item no': item_no,
                    'item name': item_name,
                    'initial qty': initial_qty,
                    'qty input': total_input,
                    'qty output': total_output,
                    'end qty': end_qty
                }
                
            except Exception as e:
                print(f"Error processing item {item_no}: {str(e)}")
                continue
        
        # Convert ke DataFrame
        if report:
            report_df = pd.DataFrame.from_dict(report, orient='index')
            report_df = report_df[['month', 'year', 'item no', 'item name', 
                                'initial qty', 'qty input', 'qty output', 'end qty']]
            return report_df
        else:
            return pd.DataFrame(columns=['month', 'year', 'item no', 'item name', 
                                    'initial qty', 'qty input', 'qty output', 'end qty'])
    
    sorted_transaction = st.session_state.transaction.sort_values(by='date', ascending=False)
    sorted_transaction['date'] = pd.to_datetime(sorted_transaction['date'])
    
    if selected_year and selected_month:
        report_data = calculate_monthly_report(sorted_transaction, selected_year, selected_month, stocklist)
        
        st.subheader(f"Monthly Report for {selected_month}-{selected_year}")
        st.dataframe(report_data, use_container_width=True)
        
        # Download CSV Monthly Report
        csv = report_data.to_csv(index=False)
        st.download_button(
            label="Download Report",
            data=csv,
            file_name=f"Monthly_Report_{selected_month}_{selected_year}.csv",
            mime="text/csv"
        )
