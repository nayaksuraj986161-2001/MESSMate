import streamlit as st, sqlite3, os, math, json
from pathlib import Path
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title='MESSMate · BH3 Shivalik Hostel', page_icon='🍽️', layout='wide')
HOSTEL='BH3 – Shivalik Hostel'
SESSION='July–December 2026'
HOSTEL_STUDENTS=250
MEAL_COSTS={'Breakfast':30,'Lunch':35,'Snacks':25,'Dinner':35}
STUDENTS=[('2025MBA-01','Aditya Sharma'),('2024MBA-03','Anshuman Tripathi'),('2025MBA-09','Prasad Biradar'),('2025MBA-018','Rohit Koshthi'),('2024MBA-016','Mohit Keenan'),('2025MBA-015','Manan Jain'),('2025MBA-022','Suraj Nayak'),('2025MBA-024','Utkarsh Kapoor')]
DB=os.getenv('MESSMATE_DB_PATH',str(Path(__file__).parent/'data'/'messmate.db'))
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
MEALS=['Breakfast','Lunch','Snacks','Dinner']
TIMES={'Breakfast':'7:30 AM – 9:30 AM','Lunch':'12:30 PM – 2:30 PM','Snacks':'5:30 PM – 6:30 PM','Dinner':'7:30 PM – 9:30 PM'}
MENU={
'Monday':{'Breakfast':'Chana Poha, Namkeen, Jalebi, Lemon, Omelette, Banana','Lunch':'Roti, Palak Matar Paneer, Rice, Lassi, Dal Fry','Snacks':'Samosa, Chutney, Chai','Dinner':'Chole, Roti, Seasonal Veg, Jeera Rice, Fry Papad, Kheer'},
'Tuesday':{'Breakfast':'Aalu Bedai, Boiled Egg/Sprouts, Banana','Lunch':'Roti, Mix Veg, Masur Dal Tadka, Rice, Papad, Dahi','Snacks':'Fried Idli, Chai','Dinner':'Kofta, Roti, Sambhar, Plain Rice, Papad'},
'Wednesday':{'Breakfast':'Pyaz Paratha + Alu Matar / Aloo Paratha + Dahi, Egg Bhurji, Green Chutney, Banana, Soya Chunks Masala','Lunch':'Rajma, Aloo Bhujia, Plain Rice, Roti, Jaali Fried Papad, Dahi','Snacks':'French Fries, Chai','Dinner':'Seasonal Veg, Roti, Veg Biryani, Arhar Dal, Halwa'},
'Thursday':{'Breakfast':'Idli, Sambhar, Boiled Egg/Sprouts, Groundnut Chutney, Banana','Lunch':'Alu puri, Kaddoo Sabzi, Veg Raita, Rice','Snacks':'Maggi, Chai','Dinner':'Paneer Bhurji, Dal Tadka, Plain Paratha, Rice'},
'Friday':{'Breakfast':'Medu Vada, Groundnut Chutney, Sambhar, Omelette, Banana','Lunch':'Kadi Chawal, Roti, Kala Chana Sabzi, Rice','Snacks':'Dabeli, Chai','Dinner':'Alu Soyabeen, Chana Dal Tadka, Rice, Roti, Gulab Jamun'},
'Saturday':{'Breakfast':'Chilla, Chilli Chana, Imli Chutney, Orange Lehsun Chutney, Boiled Egg, Banana','Lunch':'Chole Bhature, Raita, Rice, Sookha Aloo, Fried Mirchi, Lemon','Snacks':'Vermicelli (spicy), Chai','Dinner':'Roti, Mix Dal Tadka, Veg Pulao, Matar Mushroom/Khadai Paneer'},
'Sunday':{'Breakfast':'Dosa, Sambhar, Groundnut Chutney, Boiled Egg, Banana','Lunch':'Roti, Moong Dal, Rice, Seasonal Veg, Dahi','Snacks':'Chole Tikki Chat','Dinner':'Egg Curry/Egg Bhurji, Seasonal Veg, Roti, Dal Makhni, Rice, Laddu'}}

def db():
    Path(DB).parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; return c
with db() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS menu(day TEXT,meal TEXT,items TEXT,updated TEXT,PRIMARY KEY(day,meal));
    CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY,student_id TEXT,meal_date TEXT,meal TEXT,intention TEXT,created TEXT,UNIQUE(student_id,meal_date,meal));
    CREATE TABLE IF NOT EXISTS outcomes(id INTEGER PRIMARY KEY,meal_date TEXT,meal TEXT,expected INTEGER,prepared INTEGER,served INTEGER,leftover INTEGER,cost REAL,notes TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),fixed_fee REAL,meal_rate REAL,base_share REAL,policy TEXT);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT,details TEXT,created TEXT);''')
    c.execute("INSERT OR IGNORE INTO settings VALUES(1,22500,31.25,0.5,'Fixed six-month fee · Jul–Dec 2026')")
    c.execute("UPDATE settings SET fixed_fee=22500, policy='Fixed six-month fee · Jul–Dec 2026' WHERE id=1 AND fixed_fee=4500")
    for d,ms in MENU.items():
        for m,items in ms.items(): c.execute('INSERT OR IGNORE INTO menu VALUES(?,?,?,?)',(d,m,items,datetime.now().isoformat()))
    c.commit()
def read_df(sql,args=()):
    with db() as c: return pd.read_sql_query(sql,c,params=args)
def get_menu():
    df=read_df('SELECT * FROM menu'); return {(r.day,r.meal):r.items for r in df.itertuples()}
def get_res(sid=None): return read_df('SELECT * FROM reservations'+(' WHERE student_id=?' if sid else '')+' ORDER BY meal_date DESC,meal',(sid,) if sid else ())
def get_out(): return read_df('SELECT * FROM outcomes ORDER BY meal_date DESC,id DESC')
def save_res(sid,d,m,intent):
    with db() as c: c.execute('INSERT INTO reservations(student_id,meal_date,meal,intention,created) VALUES(?,?,?,?,?) ON CONFLICT(student_id,meal_date,meal) DO UPDATE SET intention=excluded.intention,created=excluded.created',(sid,d,m,intent,datetime.now().isoformat())); c.commit()
def header(k,t,sub):
    st.markdown(f'<div class="kicker">{k}</div>',unsafe_allow_html=True); st.title(t); st.write(sub)
st.markdown('''<style>@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.block-container{max-width:1500px;padding-top:1.5rem}.kicker{color:#16876b;font-weight:700;letter-spacing:.13em;font-size:.72rem}.hero{background:linear-gradient(115deg,#172d4d,#20566b);border-radius:18px;padding:1.5rem 1.8rem;color:white;margin-bottom:1rem;animation:up .45s ease}.hero h2{color:white;font-size:2rem}.hero em{color:#7ce0c4;font-style:normal}.hero p{color:#d0e1eb}div[data-testid="stMetric"]{border:1px solid #e5ebf1;background:white;border-radius:13px;padding:1rem;box-shadow:0 7px 20px #17355308}.stButton>button{border-radius:9px;font-weight:600;transition:all .18s}.stButton>button:hover{transform:translateY(-1px)}.note{background:#f0f7fb;border:1px solid #dcecf4;border-radius:10px;padding:1rem;color:#52677c}@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}</style>''',unsafe_allow_html=True)
with st.sidebar:
    st.markdown('# 🍽️ MESSMate'); st.caption('BH3 – Shivalik Hostel')
    st.caption('Session: July–December 2026')
    page=st.radio('NAVIGATION',['Dashboard','Weekly Menu','Meal Reservations','Billing','Kitchen Planning','Animated BPMN','ER Diagram'])
    st.divider(); role=st.selectbox('Demo role',['Student','Administrator'])
    if role=='Student':
        roster_options=[f'{roll} — {name}' for roll,name in STUDENTS]+['Other / not listed']
        picked=st.selectbox('Choose demo student',roster_options)
        if picked=='Other / not listed': sid=st.text_input('Enter roll number','DEMO-OTHER').strip() or 'DEMO-OTHER'
        else: sid=picked.split(' — ')[0]
    else: sid='ADMIN'; st.caption('Administrator demo view')
    st.caption('Local prototype · Not an official IIITM system')
menu=get_menu(); reservations=get_res(); outcomes=get_out()
def menuitem(day,meal): return menu.get((day,meal),'Menu not configured')
if page=='Dashboard':
    header('IIITM GWALIOR · BH3 SHIVALIK HOSTEL','Dashboard','A connected view of the fixed meal routine, semester fee, meal intentions, kitchen outcomes and process performance.')
    st.markdown('<div class="hero"><div class="kicker" style="color:#7ce0c4">MESSMATE · SMARTER MESS OPERATIONS</div><h2>Plan smarter. Waste less.<br><em>Make every meal count.</em></h2><p>BH3 – Shivalik Hostel · 250 students · July–December 2026. Keep the fixed weekly menu, improve demand visibility and evaluate billing transparency.</p></div>',unsafe_allow_html=True)
    today=date.today().isoformat(); tr=reservations[reservations.meal_date==today] if not reservations.empty else pd.DataFrame(); tout=outcomes[outcomes.meal_date==today] if not outcomes.empty else pd.DataFrame(); prep=int(tout.prepared.sum()) if not tout.empty else 0; left=int(tout.leftover.sum()) if not tout.empty else 0
    cols=st.columns(4); cols[0].metric('Hostel students',HOSTEL_STUDENTS); cols[1].metric('Semester mess fee','₹22,500',help='User-provided fixed fee for July–December 2026.'); cols[2].metric('Meal intentions today',len(tr[tr.intention=='Planning to eat']) if not tr.empty else 0); cols[3].metric('Recorded waste rate',f'{100*left/prep:.1f}%' if prep else '—')
    st.subheader('Today’s fixed meal schedule · '+date.today().strftime('%A'))
    for m in MEALS:
        with st.container(border=True): a,b=st.columns([1,4]); a.markdown(f'**{m}**'); a.caption(TIMES[m]); b.write(menuitem(date.today().strftime('%A'),m))
    if role=='Administrator':
        with st.expander('Provided student roster · 8 of 250 students'):
            st.caption('Names and roll numbers below are best-effort transcription from the handwritten image. Please verify spelling and roll-number formatting before using official records.')
            st.dataframe(pd.DataFrame([{'Roll number':r,'Student name':n} for r,n in STUDENTS]),use_container_width=True,hide_index=True)
            st.caption('The remaining 242 student records have not been provided and are not fabricated.')
    st.subheader('Recent outcomes')
    if outcomes.empty: st.info('No outcome data yet. Switch to Administrator → Kitchen Planning to record actual outcomes.')
    else:
        chart=outcomes.copy(); chart['waste_pct']=chart.apply(lambda r:100*r.leftover/r.prepared if r.prepared else 0,axis=1); st.plotly_chart(px.line(chart.sort_values('meal_date'),x='meal_date',y='waste_pct',color='meal',markers=True,labels={'waste_pct':'Waste (%)','meal_date':'Date'}),use_container_width=True)
    st.subheader('Accessible records')
    with st.expander('View today’s meal intentions',expanded=True):
        if tr.empty: st.info('No meal intentions recorded for today. Because booking is one day ahead, today’s count may be zero by design.')
        else:
            st.dataframe(tr[['student_id','meal_date','meal','intention']],use_container_width=True,hide_index=True)
            st.download_button('Download today’s intentions (CSV)',tr.to_csv(index=False).encode('utf-8'),'messmate_today_intentions.csv','text/csv')
    with st.expander('View recorded waste and production outcomes',expanded=True):
        if outcomes.empty: st.info('No saved outcomes yet. Administrator can enter them on Kitchen Planning.')
        else:
            waste_view=outcomes.copy(); waste_view['waste_rate_%']=waste_view.apply(lambda r:100*r.leftover/r.prepared if r.prepared else 0,axis=1)
            st.dataframe(waste_view[['meal_date','meal','prepared','served','leftover','waste_rate_%']],use_container_width=True,hide_index=True)
            st.download_button('Download waste records (CSV)',waste_view.to_csv(index=False).encode('utf-8'),'messmate_waste_records.csv','text/csv')
    st.markdown('<div class="note"><b>Session:</b> July–December 2026 · <b>Hostel:</b> BH3 – Shivalik Hostel · <b>Data integrity:</b> These are MESSMate records, not live data from institute attendance or billing systems.</div>',unsafe_allow_html=True)
elif page=='Weekly Menu':
    header('FIXED WEEKLY ROUTINE','Weekly Menu','Menu and timings transcribed from the BH-3 menu photo. Verify against the official notice.')
    d=st.selectbox('Choose day',DAYS); icons={'Breakfast':'🌅','Lunch':'🍛','Snacks':'☕','Dinner':'🌙'}; cols=st.columns(2)
    for i,m in enumerate(MEALS):
        with cols[i%2]:
            with st.container(border=True): st.markdown(f'### {icons[m]} {m}'); st.caption(TIMES[m]); st.write(menuitem(d,m))
    if role=='Administrator':
        with st.expander('Edit menu'):
            ed=st.selectbox('Day',DAYS,key='ed'); em=st.selectbox('Meal',MEALS,key='em'); val=st.text_area('Menu items',menuitem(ed,em))
            if st.button('Save menu change'):
                if val.strip():
                    with db() as c: c.execute('INSERT INTO menu VALUES(?,?,?,?) ON CONFLICT(day,meal) DO UPDATE SET items=excluded.items,updated=excluded.updated',(ed,em,val,datetime.now().isoformat())); c.commit()
                    st.success('Menu saved.'); st.rerun()
                else: st.error('Menu cannot be blank.')
    else: st.info('Menu editing is available in Administrator mode.')
elif page=='Meal Reservations':
    header('STUDENT WORKSPACE','Meal Reservations','Book a meal at least one day before it is served. Same-day bookings are closed so the kitchen can plan quantities in advance.')
    tomorrow=date.today()+timedelta(days=1)
    st.markdown('<div class="note"><b>Booking rule:</b> If you want to eat tomorrow, reserve the meal today. You cannot create a reservation for today.</div>',unsafe_allow_html=True)
    if role=='Student':
        with st.container(border=True):
            a,b=st.columns(2)
            d=a.date_input('Meal date (tomorrow or later)',value=tomorrow,min_value=tomorrow,max_value=date.today()+timedelta(days=30),help='Select tomorrow to book for tomorrow. Reservations must be made one day ahead.')
            m=b.selectbox('Meal slot',MEALS,format_func=lambda x:f'{x} · {TIMES[x]}')
            st.markdown(f'**{d.strftime("%A")} menu:** {menuitem(d.strftime("%A"),m)}')
            intent=st.radio('Your intention',['Planning to eat','Not planning to eat'],horizontal=True)
            if st.button('Save meal intention',type='primary'):
                if d<=date.today(): st.error('Same-day booking is closed. Please book at least one day ahead.')
                else: save_res(sid,d.isoformat(),m,intent); st.success(f'{m} intention saved for {d.strftime("%A, %d %B %Y")}.'); st.rerun()
    else:
        st.info('Administrator view: inspect reservations across the demo roster. Student bookings still follow the one-day-ahead rule.')
    r=get_res(None if role=='Administrator' else sid); st.subheader('Saved intentions')
    if r.empty: st.info('No meal intentions have been saved yet.')
    else:
        st.dataframe(r,use_container_width=True,hide_index=True)
        st.download_button('Download reservation records (CSV)',r.to_csv(index=False).encode('utf-8'),'messmate_reservations.csv','text/csv')
        if role=='Student':
            eligible=r[pd.to_datetime(r.meal_date).dt.date>date.today()]
            if not eligible.empty:
                opts={f'#{int(x.id)} · {x.meal_date} · {x.meal}':int(x.id) for _,x in eligible.iterrows()}; pick=st.selectbox('Future record to delete',list(opts))
                if st.button('Delete selected intention'):
                    with db() as c: c.execute('DELETE FROM reservations WHERE id=? AND student_id=?',(opts[pick],sid)); c.commit()
                    st.success('Reservation deleted.'); st.rerun()
    st.markdown('<div class="note"><b>Billing note:</b> A booking is a demand signal, not proof of eating. It does not change the existing fixed fee.</div>',unsafe_allow_html=True)
elif page=='Billing':
    header('BH3 SHIVALIK HOSTEL · JUL–DEC 2026','Billing & Policy Simulator','Compare the current ₹22,500 fixed semester fee with transparent alternatives. All alternatives are illustrative and do not alter official charges.')
    with db() as c: s=dict(c.execute('SELECT * FROM settings WHERE id=1').fetchone())
    if role=='Administrator':
        with st.expander('Configure simulation assumptions'):
            fee0=st.number_input('Fixed six-month fee (₹)',0.0,float(s['fixed_fee']),step=500.0); rate0=st.number_input('Average illustrative rate per meal (₹)',0.0,float(s['meal_rate']),step=1.0); share0=st.slider('Hybrid fixed-base share',0.0,1.0,float(s['base_share']),.05); policy=st.selectbox('Current policy label',['Fixed six-month fee · Jul–Dec 2026','Fixed fee with approved absence adjustment','To be verified'])
            if st.button('Save assumptions'):
                with db() as c: c.execute('UPDATE settings SET fixed_fee=?,meal_rate=?,base_share=?,policy=? WHERE id=1',(fee0,rate0,share0,policy)); c.commit()
                st.success('Saved.'); st.rerun()
        with db() as c: s=dict(c.execute('SELECT * FROM settings WHERE id=1').fetchone())
    fee=float(s['fixed_fee']); share=float(s['base_share'])
    st.write('**Current policy assumption:**',s['policy'],'— confirm the exact rules with the institute.')
    st.markdown('### Provided daily allocation')
    st.dataframe(pd.DataFrame([{'Meal':m,'Fixed time':TIMES[m],'Allocated amount/day (₹)':MEAL_COSTS[m]} for m in MEALS]),use_container_width=True,hide_index=True)
    st.metric('Total allocated per full day',f'₹{sum(MEAL_COSTS.values()):,.0f}')
    st.caption('For a like-for-like illustration, the default is 180 service days: ₹125 × 180 = ₹22,500. Change the day count if the verified billing calendar differs.')
    days=st.number_input('Planned service days in semester',min_value=1,max_value=184,value=180,step=1)
    st.markdown('### Individual meal-use assumptions')
    st.caption('Enter the number of meals one student expects to consume in the semester. The maximum for each slot is the selected service-day count.')
    cols=st.columns(4); counts={}
    for i,m in enumerate(MEALS): counts[m]=cols[i].number_input(f'{m} meals consumed',0,int(days),int(days),key='count_'+m)
    full_allocation=days*sum(MEAL_COSTS.values())
    consumed=sum(counts[m]*MEAL_COSTS[m] for m in MEALS)
    consumption=min(consumed,full_allocation)
    hybrid=fee*share+consumed*(1-share)
    rows=[
      {'Scenario':'Current fixed fee','Illustrative amount payable (₹)':fee,'Balance vs ₹22,500 (₹)':0.0,'Meaning':'Same fixed semester charge regardless of meals eaten.'},
      {'Scenario':'Consumption allocation','Illustrative amount payable (₹)':consumption,'Balance vs ₹22,500 (₹)':fee-consumption,'Meaning':'Meal allocation multiplied by meals consumed; excludes shared fixed costs.'},
      {'Scenario':'Hybrid (base + usage)','Illustrative amount payable (₹)':hybrid,'Balance vs ₹22,500 (₹)':fee-hybrid,'Meaning':f'{share:.0%} fixed base fee + {1-share:.0%} of meal-allocation value for meals consumed.'}
    ]
    cards=st.columns(3)
    for col,row in zip(cards,rows):
        col.metric(row['Scenario'],f"₹{row['Illustrative amount payable (₹)']:,.0f}",help=row['Meaning'])
        col.caption(f"Balance vs ₹22,500: ₹{row['Balance vs ₹22,500 (₹)']:,.0f}")
    st.plotly_chart(px.bar(pd.DataFrame(rows),x='Scenario',y='Illustrative amount payable (₹)',labels={'Scenario':'Billing model'}),use_container_width=True)
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.markdown(f'<div class="note"><b>What does hybrid mean?</b><br>It keeps a shared base portion ({share:.0%} × ₹{fee:,.0f} = <b>₹{fee*share:,.0f}</b>) for kitchen staffing, utilities and equipment, then adds {1-share:.0%} of the meal-allocation value for meals consumed. “Balance vs ₹22,500” is a hypothetical difference under that model, not an actual refund or money owed. A real policy needs approval, verified costs and a plan for shared expenses.</div>',unsafe_allow_html=True)
    st.subheader('Meal intention ledger')
    r=get_res(None if role=='Administrator' else sid)
    if r.empty: st.info('No meal intentions to display.')
    else: st.dataframe(r,use_container_width=True,hide_index=True)
elif page=='Kitchen Planning':
    header('BH3 SHIVALIK HOSTEL · 250 STUDENTS','Kitchen Planning','Use the provided per-meal allocation as a planning proxy—not as verified ingredient or kitchen production cost. Record actual outcomes to make analytics useful.')
    d=st.date_input('Planning date',date.today()+timedelta(days=1),min_value=date.today()); m=st.selectbox('Meal slot',MEALS,format_func=lambda x:f'{x} · {TIMES[x]}'); r=get_res(); intent_count=len(r[(r.meal_date==d.isoformat())&(r.meal==m)&(r.intention=='Planning to eat')]) if not r.empty else 0
    a,b,c=st.columns(3); expected=a.number_input('Expected attendance',0,HOSTEL_STUDENTS,HOSTEL_STUDENTS,5); walk=b.number_input('Expected walk-ins / uncertainty',0,HOSTEL_STUDENTS,0,5); buffer=c.slider('Safety buffer (%)',0,30,5)
    use=st.checkbox(f'Use saved opt-in count ({intent_count}) as demand signal',True)
    base=min(HOSTEL_STUDENTS,max(intent_count+walk,0)) if use and intent_count>0 else min(HOSTEL_STUDENTS,expected+walk)
    recommended=min(HOSTEL_STUDENTS,math.ceil(base*(1+buffer/100)))
    allocated_cost=MEAL_COSTS[m]
    st.caption(f'Planning proxy for {m}: ₹{allocated_cost} per serving, based on the allocated amount for this meal. This is not a measured ingredient cost.')
    a,b,c=st.columns(3); a.metric('Estimated demand',base); b.metric('Recommended servings',recommended); c.metric('Allocation proxy for recommended servings',f'₹{recommended*allocated_cost:,.0f}')
    st.progress(min(recommended/HOSTEL_STUDENTS,1.0),text=f'Recommendation relative to hostel capacity ({HOSTEL_STUDENTS})')
    if role=='Administrator':
        st.subheader('Record actual outcome')
        out_date=st.date_input('Outcome date',d,key='outcome_date')
        out_meal=st.selectbox('Outcome meal',MEALS,index=MEALS.index(m),key='outcome_meal')
        with st.form('outcome'):
            x1,x2,x3=st.columns(3); exp=x1.number_input('Expected demand',0,HOSTEL_STUDENTS,int(base)); prep=x2.number_input('Prepared servings',0,HOSTEL_STUDENTS,int(recommended)); served=x3.number_input('Served servings',0,HOSTEL_STUDENTS,min(int(base),int(recommended)))
            left=st.number_input('Leftover servings',0,HOSTEL_STUDENTS,max(0,int(prep)-int(served)))
            unit=st.number_input('Allocation proxy per serving (₹)',min_value=0.0,max_value=125.0,value=float(MEAL_COSTS[out_meal]),step=1.0,help='Defaults to the selected meal allocation. Replace only if you have a verified unit cost.')
            notes=st.text_input('Notes (optional)'); submit=st.form_submit_button('Save outcome',type='primary')
        if submit:
            if served+left>prep: st.error('Served + leftovers cannot exceed prepared quantity.')
            else:
                with db() as c: c.execute('INSERT INTO outcomes(meal_date,meal,expected,prepared,served,leftover,cost,notes,created) VALUES(?,?,?,?,?,?,?,?,?)',(out_date.isoformat(),out_meal,exp,prep,served,left,unit,notes,datetime.now().isoformat())); c.commit()
                st.success('Outcome saved to the MESSMate database.'); st.rerun()
    else: st.info('Switch to Administrator mode in the sidebar to enter actual production outcomes. Saved outcomes remain visible as read-only records.')
    st.subheader('Saved outcomes')
    out=get_out()
    if out.empty: st.info('No saved outcomes yet. Switch to Administrator, enter an outcome above and click “Save outcome”.')
    else:
        view=out.copy(); view['waste_rate_%']=view.apply(lambda q:100*q.leftover/q.prepared if q.prepared else 0,axis=1); view['forecast_error_%']=view.apply(lambda q:100*abs(q.prepared-q.expected)/q.expected if q.expected else 0,axis=1)
        st.dataframe(view,use_container_width=True,hide_index=True)
        st.download_button('Download saved outcomes (CSV)',view.to_csv(index=False).encode('utf-8'),'messmate_outcomes.csv','text/csv')
        st.markdown('**Waste rate** = leftovers ÷ prepared servings × 100. **Forecast error** = absolute difference between prepared and expected servings ÷ expected servings × 100.')
elif page=='Animated BPMN':
    header('PROCESS DESIGN · BPMN CONCEPT','Animated BPMN','Both process models are available below. Open either tab, then use Play, Previous, Next, Reset or click a process node to follow the flow.')
    as_is_lanes=['STUDENT / ROUTINE','MESS STAFF','KITCHEN STAFF','BILLING / RECORDS']
    as_is_nodes=[
        ('Start: meal scheduled',0,'event','A meal is due under the fixed BH3 weekly menu and published meal time.'),
        ('Attend or skip meal',0,'task','Students decide whether to attend. The current process does not yet capture opt-in meal intentions.'),
        ('Estimate demand',1,'task','Mess staff estimate demand using information available to them. This baseline should be validated with staff.'),
        ('Choose quantity',1,'task','Staff choose the production quantity based on experience and the estimated number of diners.'),
        ('Prepare food',2,'task','Kitchen staff prepare food for the planned quantity.'),
        ('Serve meal',2,'task','Meals are served during the fixed meal window.'),
        ('Observe leftovers',2,'task','Leftovers may be observed or measured depending on current recordkeeping practice.'),
        ('Apply fixed fee',3,'task','The semester fee is assumed to remain fixed. This diagram does not claim that charges are actually deducted per meal.'),
        ('End: meal cycle',3,'end','The meal service ends. Recorded demand and leftover data may be incomplete in the current-state baseline.')]
    to_be_lanes=['STUDENT','MESSMATE SYSTEM','MESS ADMIN','KITCHEN STAFF','BILLING & ANALYTICS']
    to_be_nodes=[
        ('Start: view menu',0,'event','Student checks the fixed weekly BH3 menu and meal timings.'),
        ('Book one day ahead',0,'task','Student opts in to meals for the following day before the reservation cutoff.'),
        ('Aggregate demand',1,'task','MESSMate combines valid meal intentions with historical demand and expected walk-ins.'),
        ('Recommend servings',1,'task','The system estimates production quantity using demand and a configurable safety buffer.'),
        ('Review quantity',2,'task','The administrator reviews the recommendation and can adjust it based on operational constraints.'),
        ('Approved?',2,'gateway','Yes continues to food preparation. No returns to quantity review so the estimate can be revised.'),
        ('Prepare food',3,'task','Kitchen staff prepare the approved quantity for the scheduled meal.'),
        ('Serve and record',3,'task','Staff record actual servings served. A reservation is not treated as proof of consumption.'),
        ('Record leftovers',3,'task','Staff record remaining portions using a consistent measurement method.'),
        ('Calculate KPIs',4,'task','MESSMate calculates waste rate, forecast error and estimated production cost from saved outcomes.'),
        ('End: save outcome',4,'end','The outcome is saved and can inform future planning and reporting.')]

    def render_bpmn_diagram(lanes, nodes, diagram_title):
        payload=json.dumps({'lanes':lanes,'nodes':[{'label':n[0],'lane':n[1],'type':n[2],'desc':n[3]} for n in nodes]})
        html=r'''<div style="font-family:Arial,sans-serif;color:#20334a"><style>
        #bar{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 10px}button{border:1px solid #dce5ee;background:#fff;border-radius:8px;padding:8px 12px;cursor:pointer;font-weight:600}button:hover{background:#eef8f5}
        #vp{overflow:auto;border:1px solid #dce5ee;border-radius:12px;background:#fff;background-image:radial-gradient(#e2eaf1 1px,transparent 1px);background-size:18px 18px}svg{display:block}
        .lane{fill:#fbfcfe;stroke:#d8e2ec;stroke-width:1}.lanehead{fill:#edf3f8;stroke:#d8e2ec}.lanetext{font-size:12px;font-weight:bold;fill:#526a80;text-anchor:middle}
        .flow{fill:none;stroke:#8798a9;stroke-width:2;marker-end:url(#arrow)}.flow.active{stroke:#13876e;stroke-width:3;stroke-dasharray:7 5;animation:dash .7s linear infinite}
        .task{fill:#fff;stroke:#6687ad;stroke-width:1.6;rx:9}.task.active{fill:#e1f8ef;stroke:#13876e;stroke-width:2.5}.gateway{fill:#fff3d9;stroke:#c9912f;stroke-width:2}.event{fill:#fff;stroke:#16876b;stroke-width:2.5}.end{stroke-width:4}
        .label{font-size:11px;font-weight:bold;fill:#30485f;text-anchor:middle;pointer-events:none}.eventlabel{font-size:10px;fill:#425c74;text-anchor:middle}.branch{font-size:10px;font-weight:bold;fill:#536b80}.token{fill:#e65e61;stroke:#fff;stroke-width:3;transition:cx .3s,cy .3s}#detail{margin-top:10px;padding:13px;border:1px solid #dcecf4;background:#f0f7fb;border-radius:10px;line-height:1.5}#detail b{display:block;margin-bottom:4px}@keyframes dash{to{stroke-dashoffset:-24}}@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
        </style><div id="bar"><button id="play">▶ Play</button><button id="prev">← Previous</button><button id="next">Next step →</button><button id="reset">↺ Reset</button><button id="fit">Fit width</button></div>
        <div id="vp"><svg id="diagram" role="img" aria-label="Animated BPMN process with responsibility swimlanes"></svg></div><div id="detail"><b id="title">Process start</b><span id="desc">Select a node to read its explanation.</span></div>
        <script>
        (function(){
        const D=@@DATA@@,S=document.getElementById('diagram'),NS='http://www.w3.org/2000/svg';let current=0,timer=null;
        // Horizontal BPMN: process moves left-to-right; each responsibility is a horizontal swimlane.
        const top=35,laneH=112,headH=32,left=8,nodeW=150,nodeH=46,stepX=188,headW=150;
        function el(tag,attrs,text){const x=document.createElementNS(NS,tag);Object.entries(attrs||{}).forEach(([k,v])=>x.setAttribute(k,v));if(text!==undefined)x.textContent=text;return x}
        const W=left+headW+22+D.nodes.length*stepX+20,H=top+headH+D.lanes.length*laneH+20;
        S.setAttribute('viewBox',`0 0 ${W} ${H}`);S.setAttribute('width',W);S.setAttribute('height',H);S.style.width='100%';S.style.height='auto';S.style.minWidth=Math.min(W,1100)+'px';
        const defs=el('defs'),marker=el('marker',{id:'arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:7,markerHeight:7,orient:'auto'});marker.appendChild(el('path',{d:'M0 0 L10 5 L0 10 z',fill:'#8798a9'}));defs.appendChild(marker);S.appendChild(defs);
        // Horizontal swimlanes with a fixed responsibility label rail on the left.
        D.lanes.forEach((name,i)=>{const y=top+headH+i*laneH;S.appendChild(el('rect',{x:left,y,width:W-left-8,height:laneH,class:'lane'}));S.appendChild(el('rect',{x:left,y,width:headW,height:laneH,class:'lanehead'}));
          const words=name.split(' ');let lines=[],line='';words.forEach(w=>{if((line+' '+w).trim().length>18){lines.push(line);line=w}else line=(line+' '+w).trim()});if(line)lines.push(line);lines.slice(0,2).forEach((t,j)=>S.appendChild(el('text',{x:left+headW/2,y:y+laneH/2+(j-(Math.min(lines.length,2)-1)/2)*14+4,class:'lanetext'},t)));});
        const contentLeft=left+headW+22,contentStep=stepX;
        const P=D.nodes.map((n,i)=>{const cx=contentLeft+nodeW/2+i*contentStep,cy=top+headH+n.lane*laneH+laneH/2;return {x:cx-nodeW/2,y:cy-nodeH/2,cx,cy,w:nodeW,h:nodeH}});
        // Left-to-right sequence flows; lane changes use clean orthogonal connectors.
        D.nodes.forEach((n,i)=>{if(i===0)return;const a=P[i-1],b=P[i],sx=a.cx+a.w/2,ex=b.cx-b.w/2;let d;
          if(Math.abs(a.cy-b.cy)<3)d=`M ${sx} ${a.cy} L ${ex} ${b.cy}`;
          else {const mx=(sx+ex)/2;d=`M ${sx} ${a.cy} L ${mx} ${a.cy} L ${mx} ${b.cy} L ${ex} ${b.cy}`;}
          S.appendChild(el('path',{d,class:'flow','data-flow':i}));});
        const gatewayIndex=D.nodes.findIndex(n=>n.type==='gateway');
        if(gatewayIndex>=0&&gatewayIndex>0){const a=P[gatewayIndex],b=P[gatewayIndex-1],routeY=Math.min(a.cy,b.cy)-42;const d=`M ${a.cx} ${a.cy-25} L ${a.cx} ${routeY} L ${b.cx} ${routeY} L ${b.cx} ${b.cy-nodeH/2}`;
          S.appendChild(el('path',{d,class:'flow','data-flow':'loop'}));S.appendChild(el('text',{x:(a.cx+b.cx)/2,y:routeY-7,class:'branch','text-anchor':'middle'},'NO · revise'));
          if(gatewayIndex+1<P.length)S.appendChild(el('text',{x:(a.cx+P[gatewayIndex+1].cx)/2,y:a.cy-14,class:'branch','text-anchor':'middle'},'YES'));}
        D.nodes.forEach((n,i)=>{const p=P[i],g=el('g',{'data-node':i,tabindex:'0',role:'button','aria-label':n.label,style:'cursor:pointer'});
          if(n.type==='event'||n.type==='end'){g.appendChild(el('circle',{cx:p.cx,cy:p.cy,r:16,class:'event '+(n.type==='end'?'end':'')}));g.appendChild(el('text',{x:p.cx,y:p.cy+29,class:'eventlabel'},n.label));}
          else if(n.type==='gateway'){g.appendChild(el('polygon',{points:`${p.cx},${p.cy-25} ${p.cx+25},${p.cy} ${p.cx},${p.cy+25} ${p.cx-25},${p.cy}`,class:'gateway'}));g.appendChild(el('text',{x:p.cx,y:p.cy+5,class:'label'},'X'));g.appendChild(el('text',{x:p.cx,y:p.cy+39,class:'eventlabel'},n.label));}
          else {g.appendChild(el('rect',{x:p.x,y:p.y,width:p.w,height:p.h,class:'task','data-task':i}));const words=n.label.split(' '),lines=[];let line='';words.forEach(w=>{if((line+' '+w).trim().length>19){lines.push(line);line=w}else line=(line+' '+w).trim()});if(line)lines.push(line);lines.slice(0,2).forEach((t,j)=>g.appendChild(el('text',{x:p.cx,y:p.cy+(j-(Math.min(lines.length,2)-1)/2)*13+4,class:'label'},t)));}
          g.addEventListener('click',()=>selectNode(i));g.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();selectNode(i);}});S.appendChild(g);});
        const token=el('circle',{cx:P[0].cx,cy:P[0].cy,r:7,class:'token'});S.appendChild(token);
        function selectNode(i){current=i;const n=D.nodes[i],p=P[i];document.getElementById('title').textContent=n.label;document.getElementById('desc').textContent=n.desc;token.setAttribute('cx',p.cx);token.setAttribute('cy',p.cy);S.querySelectorAll('.task').forEach(x=>x.classList.toggle('active',Number(x.dataset.task)===i));S.querySelectorAll('.flow').forEach(x=>x.classList.toggle('active',String(x.dataset.flow)===String(i)));}
        function stop(){if(timer)clearInterval(timer);timer=null;document.getElementById('play').textContent='▶ Play'}function next(){selectNode((current+1)%D.nodes.length)}
        document.getElementById('next').onclick=next;document.getElementById('prev').onclick=()=>selectNode((current-1+D.nodes.length)%D.nodes.length);document.getElementById('reset').onclick=()=>{stop();selectNode(0)};document.getElementById('play').onclick=()=>{if(timer)stop();else{document.getElementById('play').textContent='Ⅱ Pause';timer=setInterval(next,1400)}};
        document.getElementById('fit').onclick=()=>{const scale=Math.min(1,(document.getElementById('vp').clientWidth-12)/W);S.style.width=(W*scale)+'px';S.style.height=(H*scale)+'px'};selectNode(0);
        })();
        </script></div>'''.replace('@@DATA@@',payload)
        components.html(html,height=900,scrolling=True)

    as_tab,to_tab=st.tabs(['As-Is · Current workflow','To-Be · MESSMate proposal'])
    with as_tab:
        st.subheader('As-Is: current fixed-fee meal process')
        st.caption('Conceptual current-state model. Validate the exact attendance, kitchen and billing steps with mess staff before presenting it as a factual process map.')
        render_bpmn_diagram(as_is_lanes,as_is_nodes,'as-is')
        st.markdown('**Current-state issue:** students pay a fixed semester fee even if they skip a meal; meal intentions and actual consumption may not be captured in a unified record. The diagram does not assume a per-meal deduction.')
    with to_tab:
        st.subheader('To-Be: attendance-informed MESSMate process')
        st.caption('Proposed future-state model showing the one-day-ahead booking rule, demand forecast, human approval and feedback from recorded outcomes.')
        render_bpmn_diagram(to_be_lanes,to_be_nodes,'to-be')
        st.markdown('**Expected improvement:** earlier demand visibility, more transparent production planning, measurable leftovers and a data-backed discussion of billing policy options. It does not automatically change the official fee.')
    st.markdown('<div class="note"><b>How to use:</b> Open either tab, select a node or use Play / Previous / Next. The red token marks the active step. “As-Is” is a conceptual baseline; “To-Be” is a proposed design, not a live IIITM process.</div>',unsafe_allow_html=True)
else:
    header('DATA MODEL','ER Diagram','Clean animated ER model with readable entity tables, fitted relationship diamonds, and step-by-step explanations.')
    st.caption('Select Play or step through each relationship. Scroll horizontally if you are viewing on a narrow screen.')
    er_html = r'''<div id="mess-er" style="font-family:Arial,sans-serif;color:#20354a">
<style>
#mess-er *{box-sizing:border-box}#mess-er .controls{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 10px}#mess-er button{border:1px solid #d4e0ea;background:#fff;border-radius:8px;padding:8px 12px;cursor:pointer;font-weight:600;color:#20354a}#mess-er button:focus-visible{outline:3px solid #60a5fa}#mess-er button.primary{background:#176e62;color:#fff;border-color:#176e62}#mess-er .canvas{overflow:auto;border:1px solid #dce5ed;border-radius:12px;background:#fff}#mess-er svg{display:block;width:100%;min-width:850px;height:auto}#mess-er .entity{fill:#e5efff;stroke:#6d8eb3;stroke-width:1.5}#mess-er .entity.active{fill:#d7f5e9;stroke:#07866d;stroke-width:3}#mess-er .entity-title{font:bold 13px Arial,sans-serif;text-anchor:middle;fill:#203b55}#mess-er .field{font:11px Arial,sans-serif;text-anchor:middle;fill:#334b62}#mess-er .fieldline{stroke:#c2d4e7;stroke-width:1}#mess-er .connector{fill:none;stroke:#9aabba;stroke-width:1.7}#mess-er .connector.active{stroke:#12866e;stroke-width:3;stroke-dasharray:7 5;animation:erDash .7s linear infinite}#mess-er .diamond{fill:#fff0f0;stroke:#c56d6d;stroke-width:1.6}#mess-er .diamond.active{fill:#dff7ec;stroke:#07866d;stroke-width:3}#mess-er .relationship-label{font:bold 10px Arial,sans-serif;fill:#813c3c;text-anchor:middle;dominant-baseline:middle}#mess-er .relationship-label.active{fill:#08634f}#mess-er .info{margin-top:10px;padding:12px;border:1px solid #cfe8dc;background:#eff8f4;border-radius:10px;line-height:1.5}#mess-er .muted{font-size:12px;color:#64748b}@keyframes erDash{to{stroke-dashoffset:-24}}@media(prefers-reduced-motion:reduce){#mess-er *{animation:none!important}}
</style>
<div class="controls"><button id="erPlay" class="primary">▶ Play</button><button id="erPrev">← Previous</button><button id="erNext">Next relationship →</button><button id="erReset">↺ Reset</button></div>
<div class="canvas"><svg id="erSvg" viewBox="0 0 1000 700" role="img" aria-label="Animated MESSMate entity relationship diagram"></svg></div>
<div class="info" aria-live="polite"><div id="erCount" class="muted">RELATIONSHIP 1 OF 5</div><b id="erTitle">Student makes reservations</b><div id="erDesc">One student can create multiple reservations.</div><div id="erCard" class="muted" style="margin-top:6px">STUDENT 1 : N RESERVATION</div></div>
<div class="muted" style="margin-top:9px">PK = Primary Key · FK = Foreign Key · 1 : N = one-to-many. Reservations represent meal intentions, not confirmed consumption.</div>
<script>
(function(){const root=document.getElementById('mess-er');if(root.dataset.ready)return;root.dataset.ready='1';const svg=document.getElementById('erSvg'),NS='http://www.w3.org/2000/svg',by=id=>document.getElementById(id);let idx=0,timer=null;
function E(tag,a,t){const n=document.createElementNS(NS,tag);Object.entries(a||{}).forEach(([k,v])=>n.setAttribute(k,v));if(t!==undefined)n.textContent=t;return n}
const ents=[
{id:'student',name:'STUDENT',x:35,y:75,w:250,h:142,fields:['PK · student_id','name · roll_number','hostel / room','role']},
{id:'reservation',name:'RESERVATION',x:375,y:75,w:250,h:142,fields:['PK · reservation_id','FK · student_id','meal_date · meal_slot','intention_status']},
{id:'consumption',name:'CONSUMPTION',x:715,y:75,w:250,h:142,fields:['PK · consumption_id','FK · reservation_id','served_status','served_at']},
{id:'menu',name:'MENU',x:35,y:425,w:250,h:142,fields:['PK · menu_id','weekday · meal_slot','menu_items','effective_from']},
{id:'production',name:'PRODUCTION RECORD',x:375,y:425,w:250,h:142,fields:['PK · production_id','meal_date · meal_slot','prepared_qty · served_qty','leftover_qty']},
{id:'billing',name:'BILLING RECORD',x:715,y:425,w:250,h:142,fields:['PK · billing_id','FK · student_id','billing_period','fee_amount · adjustments']}
];
const rels=[
{a:'student',b:'reservation',pts:[[285,146],[375,146]],diamond:[330,146],label:['MAKES'],title:'Student makes reservations',desc:'One student can create multiple reservations. Each reservation belongs to one student.',card:'STUDENT 1 : N RESERVATION'},
{a:'reservation',b:'consumption',pts:[[625,146],[715,146]],diamond:[670,146],label:['MAY RESULT','IN'],title:'Reservation may result in consumption',desc:'A reservation records intention. A verified consumption record can be linked after the meal is served.',card:'RESERVATION 1 : 0..1 CONSUMPTION'},
{a:'menu',b:'production',pts:[[285,496],[375,496]],diamond:[330,496],label:['GUIDES'],title:'Menu guides production',desc:'The menu and meal slot guide production records for a particular date.',card:'MEAL SLOT 1 : N PRODUCTION RECORD'},
{a:'student',b:'billing',pts:[[160,217],[160,320],[840,320],[840,425]],diamond:[500,320],label:['HAS','BILLING'],title:'Student has billing records',desc:'A student can have billing records for multiple periods. Alternative billing scenarios are simulations until approved.',card:'STUDENT 1 : N BILLING RECORD'},
{a:'menu',b:'reservation',pts:[[160,425],[160,365],[500,365],[500,217]],diamond:[330,365],label:['DEFINES','MEALS'],title:'Menu defines available meals',desc:'The weekly menu defines meal slots and menu details for the date selected by the student.',card:'MENU / MEAL SLOT 1 : N RESERVATION'}
];
svg.appendChild(E('text',{x:500,y:27,'text-anchor':'middle','font-size':22,'font-weight':700,fill:'#203b55'},'MESSMate — Entity Relationship Diagram'));
svg.appendChild(E('text',{x:500,y:49,'text-anchor':'middle','font-size':11,fill:'#64748b'},'BH3 Shivalik Hostel · Conceptual database model'));
const lines=E('g');svg.appendChild(lines);
rels.forEach((r,i)=>{lines.appendChild(E('polyline',{points:r.pts.map(p=>p.join(',')).join(' '),class:'connector','data-line':i}));const [x,y]=r.diamond,rx=(i===3||i===4)?43:36,ry=25;lines.appendChild(E('polygon',{points:`${x},${y-ry} ${x+rx},${y} ${x},${y+ry} ${x-rx},${y}`,class:'diamond','data-diamond':i}));const first=y-(r.label.length-1)*5;r.label.forEach((label,j)=>lines.appendChild(E('text',{x,y:first+j*10,class:'relationship-label','data-label':i},label)));});
ents.forEach(e=>{const g=E('g',{'data-entity':e.id});g.appendChild(E('rect',{x:e.x,y:e.y,width:e.w,height:e.h,rx:8,class:'entity'}));g.appendChild(E('text',{x:e.x+e.w/2,y:e.y+24,class:'entity-title'},e.name));g.appendChild(E('line',{x1:e.x+12,y1:e.y+35,x2:e.x+e.w-12,y2:e.y+35,class:'fieldline'}));e.fields.forEach((f,j)=>g.appendChild(E('text',{x:e.x+e.w/2,y:e.y+55+j*20,class:'field'},f)));svg.appendChild(g)});
function stop(){if(timer)clearInterval(timer);timer=null;by('erPlay').textContent='▶ Play';by('erPlay').classList.add('primary')}
function select(i){idx=(i+rels.length)%rels.length;const r=rels[idx];by('erCount').textContent=`RELATIONSHIP ${idx+1} OF ${rels.length}`;by('erTitle').textContent=r.title;by('erDesc').textContent=r.desc;by('erCard').textContent=r.card;svg.querySelectorAll('[data-line]').forEach(n=>n.classList.toggle('active',+n.dataset.line===idx));svg.querySelectorAll('[data-diamond]').forEach(n=>n.classList.toggle('active',+n.dataset.diamond===idx));svg.querySelectorAll('[data-label]').forEach(n=>n.classList.toggle('active',+n.dataset.label===idx));svg.querySelectorAll('[data-entity]').forEach(n=>n.querySelector('rect').classList.toggle('active',n.dataset.entity===r.a||n.dataset.entity===r.b))}
by('erPlay').addEventListener('click',()=>{if(timer){stop();return}by('erPlay').textContent='Ⅱ Pause';by('erPlay').classList.remove('primary');timer=setInterval(()=>select(idx+1),2200)});by('erNext').addEventListener('click',()=>select(idx+1));by('erPrev').addEventListener('click',()=>select(idx-1));by('erReset').addEventListener('click',()=>{stop();select(0)});select(0)})();
</script></div>'''
    components.html(er_html, height=790, scrolling=True)
    st.markdown('**Entity relationships**')
    st.markdown('- One student can create many reservations and billing records.\n- A reservation may link to zero or one verified consumption record.\n- Menu and meal-slot details inform reservations and kitchen production records.\n- Production records store prepared, served and leftover quantities for waste analytics.')
    st.info('This is a conceptual ER diagram. Before real deployment, enforce foreign-key constraints, secure authentication, role permissions and auditable billing records.')
