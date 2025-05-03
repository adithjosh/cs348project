from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.orm import relationship
import pandas as pd
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///mls_cs348.db" #sqlite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#players
class Player(db.Model):
    #define cols using ORM
    player=db.Column(db.String(100),primary_key= True)
    team = db.Column(db.String(100),nullable=False)
    position=db.Column(db.String(50),nullable=False)
    secondary_position=db.Column(db.String(100), nullable=True)
    nation=db.Column(db.String(100))
    age=db.Column(db.Integer)
    nineties_played=db.Column(db.Float)
    goals_per_90 = db.Column(db.Float)
    assists_per_90=db.Column(db.Float)
    xg_per_90=db.Column(db.Float)
    xag_per_90 = db.Column(db.Float)
    tackles_won_pct=db.Column(db.Float)
    shot_creating_actions_per_90 = db.Column(db.Float)
    aerial_win_pct = db.Column(db.Float)
    pass_completion_rate =db.Column(db.Float)
    successful_take_on_pct = db.Column(db.Float)
    goals_per_shot=db.Column(db.Float)
    goals_per_shot_on_target=db.Column(db.Float)
    npxg_per_shot=db.Column(db.Float)
    npxg_xag_per_90= db.Column(db.Float)
    prog_passes_rec_per_90 = db.Column(db.Float)
    progressive_passes_per_90 = db.Column(db.Float)
    errors_per_90 = db.Column(db.Float)
    interceptions_per_90 = db.Column(db.Float)
    tackles_won_per_90=db.Column(db.Float)
    key_passes_per_90= db.Column(db.Float)
    assists_xag_per_90= db.Column(db.Float)
    through_balls_per_90=db.Column(db.Float)
    crosses_per_90= db.Column(db.Float)
    touches_per_90 =db.Column(db.Float)
    take_ons_attempted_per_90 =db.Column(db.Float)
    #cascade deletes:
    goalkeepers = relationship("Goalkeeper", backref="player_ref", cascade="all, delete-orphan")
    
    
class Goalkeeper(db.Model):
    #define cols using ORM
    player=db.Column(db.String(100), db.ForeignKey("player.player"),primary_key= True)    
    save_percentage  =db.Column(db.Float)
    starts = db.Column(db.Integer)
    goals_allowed_per_90 = db.Column(db.Float)
    shots_on_target_against = db.Column(db.Integer)
    saves = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    clean_sheet_pct = db.Column(db.Float)
    pk_save_pct = db.Column(db.Float)
    expected_psxg = db.Column(db.Float)
    expected_psxg_sot = db.Column(db.Float)
    psxg_ga_per_90 = db.Column(db.Float)
    pass_over_40_yards_cmp_pct = db.Column(db.Float)
    avg_pass_length = db.Column(db.Float)
    crosses_stopped_pct = db.Column(db.Float)
    wins_per_90 = db.Column(db.Float)
    expected_psxg_per_90 = db.Column(db.Float)
    saves_per_90 = db.Column(db.Float)
    shots_on_target_against_per_90 = db.Column(db.Float)
    ga_sot_per_90 = db.Column(db.Float)

with app.app_context():
    db.create_all()
    #db.session.begin
    #load data if the tables are empty cond
    if not Player.query.first():
        #players
        if os.path.exists("test_mls_players.xlsx"):
            df_players = pd.read_excel("test_mls_players.xlsx")
            df_players.rename(columns={
                "90s Played": "nineties_played","Tackles Won %": "tackles_won_pct","Aerial Win %": "aerial_win_pct","Successful Take-On %": "successful_take_on_pct", "npXG+xAG per 90": "npxg_xag_per_90", "Assists-xAG per 90": "assists_xag_per_90"
            }, inplace=True)
            df_players.columns = [col.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_") for col in df_players.columns]
            for _, row in df_players.iterrows():
                player_name = row["player"]
                if Player.query.get(player_name):
                    print(f"Skipping duplicate player: {player_name}")
                    continue
                try:
                    player = Player(**row.to_dict())
                    db.session.add(player)
                except Exception as e:
                    print(f"Error adding player {row.get('player')}: {e}")
            db.session.commit()

        #load gks
        if os.path.exists("test_mls_gk.xlsx"):
            df_gk = pd.read_excel("test_mls_gk.xlsx")
            df_gk.rename(columns={
                "Save %": "save_percentage", "PK Save %": "pk_save_pct", "Clean Sheet %":"clean_sheet_pct", "Crosses Stopped %":"crosses_stopped_pct"
            }, inplace=True)
            df_gk.columns = [col.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_") for col in df_gk.columns]
            

            for _, row in df_gk.iterrows():
                gk_name = row["player"]
                if Goalkeeper.query.get(gk_name):
                    print(f"Skipping duplicate goalkeeper: {gk_name}")
                    continue
                try:
                    gk = Goalkeeper(**row.to_dict())
                    db.session.add(gk)
                except Exception as e:
                    print(f"Error adding GK {row.get('player')}: {e}")
            db.session.commit()
            #create indexes
            index_sqls = ["CREATE INDEX IF NOT EXISTS idx_team ON Player(team)","CREATE INDEX IF NOT EXISTS idx_position ON Player(position)","CREATE INDEX IF NOT EXISTS idx_goalkeeper_player ON Goalkeeper(player)","CREATE INDEX IF NOT EXISTS idx_team_position ON Player(team, position)"]
            for s in index_sqls:
                db.session.execute(text(s))
            db.session.commit()

#Requirement 1: Add/edit/delete dynamic using ORM

@app.route("/")
def index():
    #db.session.begin
    players = Player.query.all() #auto-update changes
    gks = Goalkeeper.query.all()
    return render_template("index.html", players=players, gks=gks, Player=Player, Goalkeeper=Goalkeeper, getattr=getattr)
@app.route("/add_player",methods=["POST"])
def add_player():
    player_data = {}

    for column in Player.__table__.columns:
        col_name = column.name
        #dyanmically pull columns to fill
        if col_name == "player":  #prim key=required
            player_data[col_name] = request.form[col_name]
        elif column.type.python_type == int:
            player_data[col_name] = int(request.form.get(col_name, 0) or 0)
        elif column.type.python_type == float:
            player_data[col_name] = float(request.form.get(col_name, 0.0) or 0.0)
        else:
            player_data[col_name] = request.form.get(col_name, None)

    player = Player(**player_data) #dynamic gathering ** unpack dict
    db.session.add(player)
    db.session.commit()
    return redirect(url_for("index"))
@app.route("/add_goalkeeper",methods=["POST"])
def add_gk():
    player_name = request.form["player"]
    if not Player.query.get(player_name):
        return "Error: You must add the player first before assigning them as a goalkeeper.", 400

    gk_data = {}

    for column in Goalkeeper.__table__.columns:
        col_name = column.name
        if col_name == "player":
            gk_data[col_name] = request.form[col_name]
        elif column.type.python_type == int:
            gk_data[col_name] = int(request.form.get(col_name, 0) or 0)
        elif column.type.python_type == float:
            gk_data[col_name] = float(request.form.get(col_name, 0.0) or 0.0)
        else:
            gk_data[col_name] = request.form.get(col_name, None)

    gk = Goalkeeper(**gk_data)
    db.session.add(gk)
    db.session.commit()
    return redirect(url_for("index"))
@app.route("/delete_player/<string:player>", methods=["POST"])
def delete_player(player):
    delete= Player.query.get(player)
    if delete:
        db.session.delete(delete)
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/edit_player/<string:player_name>", methods=["GET", "POST"])
def edit_player(player_name):
    player = Player.query.get_or_404(player_name)

    if request.method == "POST":
        for column in Player.__table__.columns:
            col_name = column.name
            if col_name == "player":  #don't update PK
                continue
            if col_name in request.form:
                #get columns dynamically with existing vals
                if column.type.python_type == int:
                    setattr(player, col_name, int(request.form.get(col_name, 0) or 0))
                elif column.type.python_type == float:
                    setattr(player, col_name, float(request.form.get(col_name, 0.0) or 0.0))
                else:
                    setattr(player, col_name, request.form.get(col_name, None))

        try:
            db.session.commit()
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            return f"Error updating player: {e}", 400

    return render_template("edit_player.html", player=player, Player=Player, getattr=getattr)

@app.route("/edit_goalkeeper/<string:player_name>", methods=["GET", "POST"])
def edit_goalkeeper(player_name):
    gk = Goalkeeper.query.get_or_404(player_name)

    if request.method == "POST":
        for column in Goalkeeper.__table__.columns:
            col_name = column.name
            if col_name == "player":  #don't update FK
                continue
            if col_name in request.form:
                if column.type.python_type == int:
                    setattr(gk, col_name, int(request.form.get(col_name, 0) or 0))
                elif column.type.python_type == float:
                    setattr(gk, col_name, float(request.form.get(col_name, 0.0) or 0.0))
                else:
                    setattr(gk, col_name, request.form.get(col_name, None))

        try:
            db.session.commit()
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            return f"Error updating goalkeeper: {e}", 400

    return render_template("edit_goalkeeper.html", gk=gk, Goalkeeper=Goalkeeper, getattr=getattr)

#order cols for report
def order_cols(columns, priority=("player", "team", 'position', 'nation')):
    ordered = [col for col in priority if col in columns]
    remaining = [col for col in columns if col not in priority]
    return ordered + remaining

#Requirement 2: Prepared Statements for Report

@app.route("/report",methods=["GET"])
def report():
    teamf=request.args.get("team")
    positionf=request.args.get("position")
    columns = request.args.getlist("columns")
    #dyn pull cols
    player_cols = [col[1] for col in db.session.execute(text("PRAGMA table_info(Player)")).fetchall()]
    gk_cols = [col[1] for col in db.session.execute(text("PRAGMA table_info(Goalkeeper)")).fetchall()]
                                   
    priority_p = player_cols[:4]
    priority_g = gk_cols[:4]
    query=""
    conditions = []
    params={}
    if teamf:
        conditions.append("team = :team")
        params["team"] = teamf
    if positionf:
        conditions.append("position = :position")
        params["position"] = positionf
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    
    if positionf == "GK":
        columns=list(set(columns)&set(player_cols+gk_cols))
        if not columns:
            columns=gk_cols+player_cols[:1]
        columns = order_cols(columns)   
        if len(priority_g)>0:
            columns = order_cols(columns, priority_g)
        column_list = ", ".join([
    f"Player.{col}" if col in player_cols else f"Goalkeeper.{col}"
    for col in columns
]) #fix ambiguity error

        query= f"SELECT {column_list} FROM Goalkeeper JOIN Player ON Goalkeeper.player=Player.player"
        if teamf:
            query = query+" WHERE Player.team= :team"
            params['team']=teamf
        results = db.session.execute(text(query), params).fetchall()

        table_type = "goalkeepers"
    
    else:
        #only player colsfetched
        columns = list(set(columns) & set(player_cols)) or player_cols #valid columns
        columns = order_cols(columns)
        if len(priority_p)>0:
            columns = order_cols(columns, priority_p)
        column_list = ", ".join(columns)
        query = f"SELECT {column_list} FROM Player"
        conditions = []
        if teamf:
            conditions.append("team = :team")
            params["team"] = teamf
        if positionf:
            conditions.append("position = :position")
            params["position"] = positionf
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        results = db.session.execute(text(query), params).fetchall()

        table_type = "players"
    stats = {}
    if results:
        col_count = len(results[0])
        for i, col in enumerate(columns):
            try:
                numeric_vals = [row[i] for row in results if isinstance(row[i], (int, float)) and row[i] is not None]
                if numeric_vals:
                    stats[col] = round(sum(numeric_vals) / len(numeric_vals), 2)
            except Exception as e:
                print(f"Error computing stats for {col}: {e}")
        
    teams = db.session.query(Player.team).distinct().all()
    positions = db.session.query(Player.position).distinct().all()

    return render_template("report.html", results=results, selected_columns=columns,player_columns=player_cols, goalkeeper_columns=gk_cols,teams=teams, positions=positions, table_type= table_type,stats=stats)

#debug route
@app.route("/debug_goalkeepers")
def debug_goalkeepers():
    gks = Goalkeeper.query.all()
    return f"Loaded {len(gks)} goalkeepers: {[gk.player for gk in gks]}"

if __name__=="__main__":
    app.run(debug=True)
    
        
    
    

