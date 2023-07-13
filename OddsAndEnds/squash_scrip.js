var point_for_winning = 0;
var point_for_playing = 1;
var max_games_per_match = 5;
var max_points_per_match = max_games_per_match + 2 * point_for_playing;
var min_num_games_for_win = 3;
var min_num_points_for_win = min_num_games_for_win + point_for_playing;

function WorkoutPointsFromGame(scores, player1, num_games1, player2, num_games2)
{
  Logger.log("====WorkoutPointsFromGame====");

  if (num_games1 == min_num_games_for_win) // 1 Winner
  {
    winner = scores[player1];
    looser = scores[player2];
    looser_num_games = num_games2;
  }
  else
  {
    winner = scores[player2];
    looser = scores[player1];
    looser_num_games = num_games1;
  }
    
  Logger.log("winner: " + winner.initials);
  winner.num_games++;
  winner.num_victories++;
  winner.total_points += max_games_per_match - looser_num_games + point_for_playing + point_for_winning;
    
  looser.num_games++;
  looser.num_losses++;
  looser.total_points += looser_num_games + point_for_playing;
  Logger.log("scores (" + GetAssArrayLength(scores) + "): " + scores);
}

function GetPlayersPoints(scores, score_table)
{
  Logger.log("====GetPlayersPoints====");
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var range = ss.getRangeByName(score_table);
  var cells = range.getValues();
  Logger.log("The range has " + cells.length + " rows and " + cells[0].length + " columns");
  
  var total_points = 0;
  var num_matches = 0;
  var num_victories = 0;
  var num_losses = 0;
  for (var i = 0; i < cells.length; ++i)
  {
    for (var j = 0; j < cells[i].length; ++j)
    {
      var cell = cells[i][j];
      var string = '(\\w+):(\\d+)\\s+(\\w+):(\\d+)';
      var pattern = new RegExp(string, "ig");
      var games_details = pattern.exec(TrimAll(cell.toString()));

      if (games_details && games_details.length == 5)
      {
        Logger.log("games_details: " + games_details);
        WorkoutPointsFromGame(scores, games_details[1], parseInt(games_details[2]), games_details[3], parseInt(games_details[4]));
      }
    }
  }    
}

function PlayerData(initials, fullname)
{
  this.initials = initials;
  var fullname_split = fullname.split(" ");
  this.surname = fullname_split.pop();
  this.firstname = fullname_split.join(" ");
  this.total_points = 0;
  this.num_games = 0;
  this.num_victories = 0;
  this.num_losses = 0;
}

function PrintAssocArray(associative_array)
{
  for (i in associative_array)
  {
    Logger.log(i);
  }
}

function sort_assoc(aInput)
{
  var aTemp = [];
  for (var sKey in aInput)
    aTemp.push([sKey, aInput[sKey]]);
  
  aTemp.sort(function ()
             {
               // First most points, then least matches, then most wins, then least losses, then least name
               var res = arguments[0][1].total_points == arguments[1][1].total_points;
               if (!res)
                 return arguments[0][1].total_points > arguments[1][1].total_points;
               res = arguments[0][1].num_games == arguments[1][1].num_games;
               if (!res)
                 return arguments[0][1].num_games <= arguments[1][1].num_games;
               res = arguments[0][1].num_victories == arguments[1][1].num_victories;
               if (!res)
                 return arguments[0][1].num_victories > arguments[1][1].num_victories;
               res = arguments[0][1].num_losses == arguments[1][1].num_losses;
               if (!res)
                 return arguments[0][1].num_losses <= arguments[1][1].num_losses;
               return arguments[0][1].firstname <= arguments[1][1].firstname;             }
            );
  var aOutput = [];
  for (var nIndex = aTemp.length-1; nIndex >=0; nIndex--)
    aOutput[aTemp[nIndex][0]] = aTemp[nIndex][1];
  
  return aOutput;
}

function GetAssArrayLength(an_array)
{
  var size = 0;
  for (stuff in an_array)  
    size++;
  return size;
}

function TrimAll(sString)
{
  while (sString.substring(0,1) == ' ')
  {
    sString = sString.substring(1, sString.length);
  }
  while (sString.substring(sString.length-1, sString.length) == ' ')
  {
    sString = sString.substring(0,sString.length-1);
  }
  return sString;
}

function MakeAssocArray(a)
{
  var o = {};
  for(var i=0;i<a.length;i++)
  {
    o[a[i]]='';
  }
  return o;
}

function CheckScores(players_region, score_table_region)
{
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  range = ss.getRangeByName(players_region);
  var players = range.getValues();
  
  var temp_initials = [];
  for (var i = 0; i < players.length; i++)
  {
    temp_initials.push(players[i][0]);
  }
  var initials = MakeAssocArray(temp_initials);
  PrintAssocArray(initials);
  
  var range = ss.getRangeByName(score_table_region);
  var cells = range.getValues();
  var result = true;

  for (var i = 0; i < cells.length; ++i)
  {
    for (var j = 0; j < cells[i].length; ++j)
    {
      var cell = TrimAll((cells[i][j]).toString());
      if (!cell)
        continue;
      //Logger.log("Cell: " + cell);
      var string = '(\\w+):(\\d+) (\\w+):(\\d+)';
      var pattern = new RegExp(string, "ig");
      var match = pattern.exec(cell);
      if (!match ||
          match.length != 5)
      {
        Browser.msgBox("The entry \""+cell+"\" doesn't seem correct, either the names or the format are not recognised.\n");
        result = false;
      }
      else if (!(match[1] in initials) || !(match[3] in initials))
      {
        Browser.msgBox("The initials in \""+cell+"\" are not correct.\n");
        result = false;
      }
      else if (
          parseInt(match[2]) < 0 || parseInt(match[2]) > min_num_games_for_win ||
          parseInt(match[4]) < 0 || parseInt(match[4]) > min_num_games_for_win ||
          (parseInt(match[2]) < min_num_games_for_win && parseInt(match[4]) < min_num_games_for_win)
         )
      {
        Browser.msgBox("The scores in \""+cell+"\" don't seem correct.\n" +
                       "Scores should be between 0 and 3 and only one player should have 3.\n");
        result = false;
      }
    }
  }    
  return result;
}

function RefreshLeagueTable(initials, score_table, league_table_title, league_table)
{
  var scores = {};

  Logger.log("initials: " + initials);
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var range = ss.getRangeByName(initials);
  var players = range.getValues();
  
  // initiate player data
  for (var i = 0; i < players.length; ++i)
  {
    scores[players[i][0]] = new PlayerData(players[i][0], players[i][1]);
  }
 
  
  if (CheckScores(initials, score_table))
    GetPlayersPoints(scores, score_table);
  //Logger.log("--scores (" + GetAssArrayLength(scores) + "): " + scores);

  // Workout stats
  sorted_scores = sort_assoc(scores);
  var league_table_data = [];
  var total_num_games = (players.length*2 - 2);
  var tournament_total_games = players.length * (players.length - 1);
  var tournament_game_played = 0;
  for (name in sorted_scores)
  {
    Logger.log("Sorted score: " + name);
    var player = sorted_scores[name];
    var text = player.firstname + " - " + player.total_points + " pts" +
        " ("+ player.num_victories + "w, " + player.num_losses + "l, " +
        player.num_games +"/" + total_num_games + ", "+
        (player.total_points/player.num_games).toFixed(1)+" avg)";
    tournament_game_played += player.num_games;
    Logger.log(text);
    league_table_data.push([text]);
  }
  tournament_game_played = tournament_game_played/2; //all the games were counted twice
  
  // Empty the league table
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var league_table_range = ss.getRangeByName(league_table);
  league_table_range.clearContent();
  // Fill it
  var league_table_range = ss.getRangeByName(league_table);
  league_table_range.setValues(league_table_data);
  // update the title
  var league_table_title = ss.getRangeByName(league_table_title);
  league_table_title.setValues([["League Table " + (tournament_game_played*100/tournament_total_games).toFixed(0) + "% complete"]]);
}
          
function RefreshLeagueTables()
{
  RefreshLeagueTable("initials_1", "scores_1", "league_table_title_1", "league_table_entries_1");
  RefreshLeagueTable("initials_2", "scores_2", "league_table_title_2", "league_table_entries_2");
}

function onOpen(event)
{
  RefreshLeagueTables();  
}           

function onEdit(event)
{
  RefreshLeagueTables();  
}

