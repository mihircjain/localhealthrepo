import os
from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.models.chat import UserQuery, Insight
from src.models.data_source import DataSource, UserDataSource
from src.models.activity import Activity
from src.models.food import FoodEntry, FoodItem
from src.models.sleep import SleepRecord
from src.models.blood_report import BloodReport, BloodMetric
from src.models.medication import UserMedication, MedicationLog, Medication
from src.models.workout import Workout, WorkoutExercise, Exercise
from datetime import datetime, timedelta
import json
import re
from sqlalchemy import func, desc, and_, or_

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/query', methods=['POST'])
def process_query():
    """Process a user query and return a response based on their health data"""
    user_id = request.json.get('user_id')
    query_text = request.json.get('query')
    
    if not user_id or not query_text:
        return jsonify({"error": "User ID and query text are required"}), 400
    
    # Create a record of the query
    user_query = UserQuery(
        user_id=user_id,
        query_text=query_text,
        query_time=datetime.utcnow()
    )
    db.session.add(user_query)
    db.session.commit()
    
    try:
        # Process the query and generate a response
        response, data_sources_used = generate_response(user_id, query_text)
        
        # Update the query record with the response
        user_query.response_text = response
        user_query.data_sources_used = data_sources_used
        db.session.commit()
        
        return jsonify({
            "success": True,
            "query_id": user_query.id,
            "response": response,
            "data_sources_used": data_sources_used
        })
    except Exception as e:
        # Update the query record with the error
        user_query.response_text = f"Error processing query: {str(e)}"
        db.session.commit()
        
        return jsonify({
            "error": f"Failed to process query: {str(e)}"
        }), 500

@chat_bp.route('/history', methods=['GET'])
def get_query_history():
    """Get chat history for a user"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get query history
    queries = UserQuery.query.filter_by(user_id=user_id) \
                            .order_by(UserQuery.query_time.desc()) \
                            .limit(limit).offset(offset).all()
    
    return jsonify({
        "success": True,
        "queries": [query.to_dict() for query in queries],
        "total": UserQuery.query.filter_by(user_id=user_id).count()
    })

@chat_bp.route('/insights', methods=['GET'])
def get_insights():
    """Get insights for a user"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get insights
    insights = Insight.query.filter_by(user_id=user_id) \
                          .order_by(Insight.relevance_score.desc()) \
                          .limit(limit).offset(offset).all()
    
    return jsonify({
        "success": True,
        "insights": [insight.to_dict() for insight in insights],
        "total": Insight.query.filter_by(user_id=user_id).count()
    })

@chat_bp.route('/generate-insights', methods=['POST'])
def generate_user_insights():
    """Generate insights for a user based on their health data"""
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        # Generate insights
        insights = create_insights_for_user(user_id)
        
        return jsonify({
            "success": True,
            "message": f"Generated {len(insights)} insights",
            "insights": [insight.to_dict() for insight in insights]
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to generate insights: {str(e)}"
        }), 500

@chat_bp.route('/mark-insight-read', methods=['POST'])
def mark_insight_read():
    """Mark an insight as read"""
    insight_id = request.json.get('insight_id')
    
    if not insight_id:
        return jsonify({"error": "Insight ID is required"}), 400
    
    insight = Insight.query.get(insight_id)
    if not insight:
        return jsonify({"error": "Insight not found"}), 404
    
    insight.is_read = True
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Insight marked as read"
    })

def generate_response(user_id, query_text):
    """Generate a response to a user query based on their health data"""
    # Normalize query text
    query_text = query_text.lower().strip()
    
    # Track which data sources are used
    data_sources_used = []
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return "User not found", data_sources_used
    
    # Determine query intent
    intent = determine_query_intent(query_text)
    
    # Process query based on intent
    if intent == 'activity':
        response, sources = process_activity_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'food':
        response, sources = process_food_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'sleep':
        response, sources = process_sleep_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'blood':
        response, sources = process_blood_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'medication':
        response, sources = process_medication_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'workout':
        response, sources = process_workout_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'summary':
        response, sources = process_summary_query(user_id, query_text)
        data_sources_used.extend(sources)
    elif intent == 'comparison':
        response, sources = process_comparison_query(user_id, query_text)
        data_sources_used.extend(sources)
    else:
        # Default response for unrecognized queries
        response = "I'm not sure how to answer that question. You can ask me about your activities, food, sleep, blood reports, medications, or workouts. For example, 'How was my sleep last week?' or 'What was my average heart rate during my last run?'"
    
    return response, list(set(data_sources_used))  # Remove duplicates

def determine_query_intent(query_text):
    """Determine the intent of a user query"""
    # Define keywords for each intent
    intent_keywords = {
        'activity': ['activity', 'activities', 'run', 'running', 'walk', 'walking', 'cycle', 'cycling', 'steps', 'distance', 'strava'],
        'food': ['food', 'eat', 'eating', 'nutrition', 'diet', 'calories', 'carbs', 'protein', 'fat', 'meal', 'breakfast', 'lunch', 'dinner', 'snack', 'healthifyme'],
        'sleep': ['sleep', 'slept', 'bedtime', 'wake', 'rem', 'deep', 'light', 'apple health', 'oura', 'fitbit'],
        'blood': ['blood', 'test', 'report', 'cholesterol', 'glucose', 'hemoglobin', 'lab'],
        'medication': ['medication', 'medicine', 'pill', 'drug', 'prescription', 'dose', 'dosage'],
        'workout': ['workout', 'exercise', 'gym', 'weight', 'strength', 'training', 'hevy', 'bench', 'squat', 'deadlift'],
        'summary': ['summary', 'overall', 'health', 'status', 'dashboard', 'overview'],
        'comparison': ['compare', 'comparison', 'versus', 'vs', 'difference', 'between', 'than']
    }
    
    # Check for time-related keywords
    time_keywords = ['today', 'yesterday', 'week', 'month', 'year', 'last', 'this', 'past', 'recent']
    
    # Count matches for each intent
    intent_scores = {intent: 0 for intent in intent_keywords}
    
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in query_text:
                intent_scores[intent] += 1
    
    # If we have a clear winner, return that intent
    max_score = max(intent_scores.values())
    if max_score > 0:
        # Get all intents with the max score
        top_intents = [intent for intent, score in intent_scores.items() if score == max_score]
        if len(top_intents) == 1:
            return top_intents[0]
    
    # If no clear intent or tie, check for specific patterns
    if 'compare' in query_text or ' vs ' in query_text or 'versus' in query_text:
        return 'comparison'
    
    if any(word in query_text for word in ['summary', 'overview', 'dashboard']):
        return 'summary'
    
    # Default to summary if no clear intent
    return 'summary'

def process_activity_query(user_id, query_text):
    """Process a query about activities"""
    data_sources_used = []
    
    # Get Strava data source
    strava_source = DataSource.query.filter_by(name="Strava").first()
    if strava_source:
        data_sources_used.append("Strava")
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Query activities
    activities = Activity.query.filter(
        Activity.user_id == user_id,
        Activity.start_time >= start_date,
        Activity.start_time <= end_date
    ).order_by(Activity.start_time.desc()).all()
    
    if not activities:
        return f"I couldn't find any activities in the specified time range ({time_range}).", data_sources_used
    
    # Check for specific metrics
    if 'steps' in query_text:
        total_steps = sum(activity.distance * 1.31 for activity in activities if activity.distance)  # Rough conversion from meters to steps
        avg_steps = total_steps / len(activities) if activities else 0
        return f"You took approximately {int(total_steps)} steps in total during this period, averaging {int(avg_steps)} steps per activity.", data_sources_used
    
    if 'distance' in query_text:
        total_distance = sum(activity.distance for activity in activities if activity.distance)
        avg_distance = total_distance / len(activities) if activities else 0
        return f"You covered {total_distance/1000:.2f} km in total during this period, averaging {avg_distance/1000:.2f} km per activity.", data_sources_used
    
    if 'heart rate' in query_text or 'heartrate' in query_text:
        activities_with_hr = [a for a in activities if a.average_heart_rate]
        if not activities_with_hr:
            return "I couldn't find any heart rate data for your activities in this period.", data_sources_used
        
        avg_hr = sum(a.average_heart_rate for a in activities_with_hr) / len(activities_with_hr)
        max_hr = max(a.max_heart_rate for a in activities_with_hr if a.max_heart_rate)
        return f"Your average heart rate during activities was {avg_hr:.0f} bpm, with a maximum of {max_hr:.0f} bpm.", data_sources_used
    
    if 'calories' in query_text:
        activities_with_calories = [a for a in activities if a.calories]
        if not activities_with_calories:
            return "I couldn't find any calorie data for your activities in this period.", data_sources_used
        
        total_calories = sum(a.calories for a in activities_with_calories)
        avg_calories = total_calories / len(activities_with_calories)
        return f"You burned approximately {total_calories:.0f} calories in total during this period, averaging {avg_calories:.0f} calories per activity.", data_sources_used
    
    # Default summary
    activity_types = {}
    for activity in activities:
        activity_type = activity.activity_type
        if activity_type in activity_types:
            activity_types[activity_type] += 1
        else:
            activity_types[activity_type] = 1
    
    total_duration = sum(activity.duration for activity in activities if activity.duration)
    total_distance = sum(activity.distance for activity in activities if activity.distance)
    
    activity_summary = ", ".join([f"{count} {activity_type}" for activity_type, count in activity_types.items()])
    
    response = f"During this period ({time_range}), you completed {len(activities)} activities ({activity_summary}). "
    response += f"You spent {total_duration//3600} hours and {(total_duration%3600)//60} minutes exercising, "
    response += f"covering a total distance of {total_distance/1000:.2f} km."
    
    return response, data_sources_used

def process_food_query(user_id, query_text):
    """Process a query about food and nutrition"""
    data_sources_used = []
    
    # Get HealthifyMe data source
    healthifyme_source = DataSource.query.filter_by(name="HealthifyMe").first()
    if healthifyme_source:
        data_sources_used.append("HealthifyMe")
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Query food entries
    food_entries = FoodEntry.query.filter(
        FoodEntry.user_id == user_id,
        FoodEntry.consumed_at >= start_date,
        FoodEntry.consumed_at <= end_date
    ).order_by(FoodEntry.consumed_at.desc()).all()
    
    if not food_entries:
        return f"I couldn't find any food entries in the specified time range ({time_range}).", data_sources_used
    
    # Check for specific metrics
    if 'calories' in query_text:
        total_calories = sum(entry.total_calories for entry in food_entries if entry.total_calories)
        avg_calories = total_calories / len(food_entries) if food_entries else 0
        return f"You consumed approximately {total_calories:.0f} calories in total during this period, averaging {avg_calories:.0f} calories per day.", data_sources_used
    
    if 'protein' in query_text:
        total_protein = sum(entry.total_protein for entry in food_entries if entry.total_protein)
        avg_protein = total_protein / len(food_entries) if food_entries else 0
        return f"You consumed approximately {total_protein:.0f}g of protein in total during this period, averaging {avg_protein:.0f}g per day.", data_sources_used
    
    if 'carbs' in query_text or 'carbohydrates' in query_text:
        total_carbs = sum(entry.total_carbs for entry in food_entries if entry.total_carbs)
        avg_carbs = total_carbs / len(food_entries) if food_entries else 0
        return f"You consumed approximately {total_carbs:.0f}g of carbohydrates in total during this period, averaging {avg_carbs:.0f}g per day.", data_sources_used
    
    if 'fat' in query_text:
        total_fat = sum(entry.total_fat for entry in food_entries if entry.total_fat)
        avg_fat = total_fat / len(food_entries) if food_entries else 0
        return f"You consumed approximately {total_fat:.0f}g of fat in total during this period, averaging {avg_fat:.0f}g per day.", data_sources_used
    
    # Check for meal type queries
    meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
    for meal_type in meal_types:
        if meal_type in query_text:
            meal_entries = [entry for entry in food_entries if entry.meal_type == meal_type]
            if not meal_entries:
                return f"I couldn't find any {meal_type} entries in the specified time range ({time_range}).", data_sources_used
            
            avg_calories = sum(entry.total_calories for entry in meal_entries if entry.total_calories) / len(meal_entries)
            
            # Get common foods
            food_items = []
            for entry in meal_entries:
                food_items.extend(FoodItem.query.filter_by(food_entry_id=entry.id).all())
            
            food_counts = {}
            for item in food_items:
                if item.name in food_counts:
                    food_counts[item.name] += 1
                else:
                    food_counts[item.name] = 1
            
            common_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            common_foods_str = ", ".join([food for food, count in common_foods])
            
            return f"For {meal_type}, you consumed an average of {avg_calories:.0f} calories. Your most common foods were {common_foods_str}.", data_sources_used
    
    # Default summary
    total_calories = sum(entry.total_calories for entry in food_entries if entry.total_calories)
    total_protein = sum(entry.total_protein for entry in food_entries if entry.total_protein)
    total_carbs = sum(entry.total_carbs for entry in food_entries if entry.total_carbs)
    total_fat = sum(entry.total_fat for entry in food_entries if entry.total_fat)
    
    # Calculate daily averages
    days = (end_date - start_date).days + 1
    avg_calories = total_calories / days
    avg_protein = total_protein / days
    avg_carbs = total_carbs / days
    avg_fat = total_fat / days
    
    response = f"During this period ({time_range}), you consumed an average of {avg_calories:.0f} calories per day, "
    response += f"with {avg_protein:.0f}g of protein, {avg_carbs:.0f}g of carbohydrates, and {avg_fat:.0f}g of fat. "
    
    # Get meal type distribution
    meal_counts = {}
    for entry in food_entries:
        if entry.meal_type in meal_counts:
            meal_counts[entry.meal_type] += 1
        else:
            meal_counts[entry.meal_type] = 1
    
    meal_summary = ", ".join([f"{count} {meal_type}s" for meal_type, count in meal_counts.items()])
    response += f"You logged {len(food_entries)} meals in total ({meal_summary})."
    
    return response, data_sources_used

def process_sleep_query(user_id, query_text):
    """Process a query about sleep"""
    data_sources_used = []
    
    # Get sleep data sources
    sleep_sources = DataSource.query.filter_by(source_type="sleep").all()
    for source in sleep_sources:
        data_sources_used.append(source.name)
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Query sleep records
    sleep_records = SleepRecord.query.filter(
        SleepRecord.user_id == user_id,
        SleepRecord.start_time >= start_date,
        SleepRecord.start_time <= end_date
    ).order_by(SleepRecord.start_time.desc()).all()
    
    if not sleep_records:
        return f"I couldn't find any sleep records in the specified time range ({time_range}).", data_sources_used
    
    # Check for specific metrics
    if 'deep sleep' in query_text:
        records_with_deep = [r for r in sleep_records if r.deep_sleep_duration]
        if not records_with_deep:
            return "I couldn't find any deep sleep data for this period.", data_sources_used
        
        avg_deep = sum(r.deep_sleep_duration for r in records_with_deep) / len(records_with_deep)
        return f"You averaged {avg_deep/3600:.1f} hours of deep sleep per night during this period.", data_sources_used
    
    if 'rem' in query_text:
        records_with_rem = [r for r in sleep_records if r.rem_sleep_duration]
        if not records_with_rem:
            return "I couldn't find any REM sleep data for this period.", data_sources_used
        
        avg_rem = sum(r.rem_sleep_duration for r in records_with_rem) / len(records_with_rem)
        return f"You averaged {avg_rem/3600:.1f} hours of REM sleep per night during this period.", data_sources_used
    
    if 'heart rate' in query_text or 'heartrate' in query_text:
        records_with_hr = [r for r in sleep_records if r.heart_rate_avg]
        if not records_with_hr:
            return "I couldn't find any heart rate data during sleep for this period.", data_sources_used
        
        avg_hr = sum(r.heart_rate_avg for r in records_with_hr) / len(records_with_hr)
        min_hr = min(r.heart_rate_min for r in records_with_hr if r.heart_rate_min)
        return f"Your average heart rate during sleep was {avg_hr:.0f} bpm, with a minimum of {min_hr:.0f} bpm.", data_sources_used
    
    if 'score' in query_text:
        records_with_score = [r for r in sleep_records if r.sleep_score]
        if not records_with_score:
            return "I couldn't find any sleep score data for this period.", data_sources_used
        
        avg_score = sum(r.sleep_score for r in records_with_score) / len(records_with_score)
        max_score = max(r.sleep_score for r in records_with_score)
        max_date = next(r.start_time.strftime('%A, %B %d') for r in records_with_score if r.sleep_score == max_score)
        
        return f"Your average sleep score was {avg_score:.0f}/100. Your best night was {max_date} with a score of {max_score}.", data_sources_used
    
    # Default summary
    total_duration = sum(record.duration for record in sleep_records if record.duration)
    avg_duration = total_duration / len(sleep_records) if sleep_records else 0
    
    # Calculate averages for sleep phases
    records_with_deep = [r for r in sleep_records if r.deep_sleep_duration]
    avg_deep = sum(r.deep_sleep_duration for r in records_with_deep) / len(records_with_deep) if records_with_deep else 0
    
    records_with_light = [r for r in sleep_records if r.light_sleep_duration]
    avg_light = sum(r.light_sleep_duration for r in records_with_light) / len(records_with_light) if records_with_light else 0
    
    records_with_rem = [r for r in sleep_records if r.rem_sleep_duration]
    avg_rem = sum(r.rem_sleep_duration for r in records_with_rem) / len(records_with_rem) if records_with_rem else 0
    
    records_with_score = [r for r in sleep_records if r.sleep_score]
    avg_score = sum(r.sleep_score for r in records_with_score) / len(records_with_score) if records_with_score else None
    
    response = f"During this period ({time_range}), you slept an average of {avg_duration/3600:.1f} hours per night. "
    
    if avg_deep > 0:
        response += f"Your sleep consisted of {avg_deep/3600:.1f} hours of deep sleep, "
    if avg_light > 0:
        response += f"{avg_light/3600:.1f} hours of light sleep, "
    if avg_rem > 0:
        response += f"and {avg_rem/3600:.1f} hours of REM sleep. "
    
    if avg_score:
        response += f"Your average sleep score was {avg_score:.0f}/100."
    
    return response, data_sources_used

def process_blood_query(user_id, query_text):
    """Process a query about blood reports"""
    data_sources_used = ["Blood Reports"]
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Query blood reports
    blood_reports = BloodReport.query.filter(
        BloodReport.user_id == user_id,
        BloodReport.report_date >= start_date.date(),
        BloodReport.report_date <= end_date.date()
    ).order_by(BloodReport.report_date.desc()).all()
    
    if not blood_reports:
        return f"I couldn't find any blood reports in the specified time range ({time_range}).", data_sources_used
    
    # Check for specific metrics
    metrics_of_interest = [
        ('cholesterol', ['cholesterol', 'ldl', 'hdl']),
        ('glucose', ['glucose', 'blood sugar']),
        ('hemoglobin', ['hemoglobin', 'hgb', 'hb']),
        ('white blood cell', ['white blood cell', 'wbc']),
        ('red blood cell', ['red blood cell', 'rbc']),
        ('platelet', ['platelet']),
        ('vitamin d', ['vitamin d']),
        ('vitamin b12', ['vitamin b12']),
        ('iron', ['iron']),
        ('thyroid', ['thyroid', 'tsh', 't3', 't4'])
    ]
    
    for metric_name, keywords in metrics_of_interest:
        if any(keyword in query_text for keyword in keywords):
            # Find all metrics matching this category
            all_metrics = []
            for report in blood_reports:
                report_metrics = BloodMetric.query.filter(
                    BloodMetric.blood_report_id == report.id,
                    BloodMetric.metric_name.ilike(f'%{metric_name}%')
                ).all()
                
                for metric in report_metrics:
                    all_metrics.append({
                        'name': metric.metric_name,
                        'value': metric.metric_value,
                        'unit': metric.unit,
                        'reference_range': metric.reference_range,
                        'is_normal': metric.is_normal,
                        'date': report.report_date
                    })
            
            if not all_metrics:
                return f"I couldn't find any {metric_name} data in your blood reports for this period.", data_sources_used
            
            # Sort by date, most recent first
            all_metrics.sort(key=lambda x: x['date'], reverse=True)
            latest = all_metrics[0]
            
            response = f"Your most recent {latest['name']} level was {latest['value']} {latest['unit']} on {latest['date'].strftime('%B %d, %Y')}. "
            
            if latest['reference_range']:
                response += f"The reference range is {latest['reference_range']} {latest['unit']}. "
            
            if latest['is_normal'] is not None:
                if latest['is_normal']:
                    response += "This is within the normal range."
                else:
                    response += "This is outside the normal range."
            
            # If we have historical data, show trend
            if len(all_metrics) > 1:
                oldest = all_metrics[-1]
                change = latest['value'] - oldest['value']
                change_pct = (change / oldest['value']) * 100
                
                if abs(change_pct) > 5:  # Only mention if change is significant
                    if change > 0:
                        response += f" Your {latest['name']} has increased by {abs(change):.1f} {latest['unit']} ({abs(change_pct):.1f}%) since {oldest['date'].strftime('%B %d, %Y')}."
                    else:
                        response += f" Your {latest['name']} has decreased by {abs(change):.1f} {latest['unit']} ({abs(change_pct):.1f}%) since {oldest['date'].strftime('%B %d, %Y')}."
            
            return response, data_sources_used
    
    # Default summary
    latest_report = blood_reports[0]
    metrics = BloodMetric.query.filter_by(blood_report_id=latest_report.id).all()
    
    abnormal_metrics = [m for m in metrics if m.is_normal is False]
    
    response = f"Your most recent blood report is from {latest_report.report_date.strftime('%B %d, %Y')}. "
    
    if latest_report.report_provider:
        response += f"It was provided by {latest_report.report_provider}. "
    
    response += f"The report includes {len(metrics)} different metrics. "
    
    if abnormal_metrics:
        abnormal_names = [m.metric_name for m in abnormal_metrics]
        response += f"The following metrics were outside the normal range: {', '.join(abnormal_names)}."
    else:
        response += "All metrics were within normal ranges."
    
    return response, data_sources_used

def process_medication_query(user_id, query_text):
    """Process a query about medications"""
    data_sources_used = ["Medications"]
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Get user medications
    user_medications = UserMedication.query.filter_by(user_id=user_id).all()
    
    if not user_medications:
        return "You don't have any medications tracked in the system.", data_sources_used
    
    # Get medication logs
    medication_logs = []
    for um in user_medications:
        logs = MedicationLog.query.filter(
            MedicationLog.user_medication_id == um.id,
            MedicationLog.taken_at >= start_date,
            MedicationLog.taken_at <= end_date
        ).all()
        
        for log in logs:
            medication = Medication.query.get(um.medication_id)
            medication_logs.append({
                'name': medication.name if medication else 'Unknown',
                'custom_name': um.custom_name,
                'dosage': log.dosage_taken or um.dosage,
                'taken_at': log.taken_at
            })
    
    if not medication_logs:
        return f"I couldn't find any medication logs in the specified time range ({time_range}).", data_sources_used
    
    # Check for specific medication
    for um in user_medications:
        medication = Medication.query.get(um.medication_id)
        if medication and medication.name.lower() in query_text:
            # Filter logs for this medication
            med_logs = [log for log in medication_logs if log['name'].lower() == medication.name.lower()]
            
            if not med_logs:
                return f"I couldn't find any logs for {medication.name} in the specified time range ({time_range}).", data_sources_used
            
            adherence_rate = len(med_logs) / ((end_date - start_date).days + 1)
            if 'daily' in um.frequency.lower():
                adherence_rate *= 100  # Convert to percentage for daily medications
                return f"You took {medication.name} {len(med_logs)} times during this period, with an adherence rate of {adherence_rate:.0f}% for your daily schedule.", data_sources_used
            else:
                return f"You took {medication.name} {len(med_logs)} times during this period, averaging {adherence_rate:.1f} doses per day.", data_sources_used
    
    # Default summary
    medication_counts = {}
    for log in medication_logs:
        name = log['custom_name'] or log['name']
        if name in medication_counts:
            medication_counts[name] += 1
        else:
            medication_counts[name] = 1
    
    most_frequent = sorted(medication_counts.items(), key=lambda x: x[1], reverse=True)
    
    response = f"During this period ({time_range}), you took {len(medication_logs)} medication doses in total. "
    
    if most_frequent:
        response += "Your most frequently taken medications were: "
        for name, count in most_frequent[:3]:
            response += f"{name} ({count} times), "
        response = response.rstrip(', ') + ". "
    
    # Calculate adherence rate if we have frequency information
    daily_meds = [um for um in user_medications if um.frequency and 'daily' in um.frequency.lower()]
    if daily_meds:
        days = (end_date - start_date).days + 1
        expected_doses = len(daily_meds) * days
        actual_doses = sum(count for name, count in medication_counts.items())
        adherence_rate = (actual_doses / expected_doses) * 100
        
        response += f"Your overall medication adherence rate was {adherence_rate:.0f}%."
    
    return response, data_sources_used

def process_workout_query(user_id, query_text):
    """Process a query about workouts"""
    data_sources_used = []
    
    # Get Hevy data source
    hevy_source = DataSource.query.filter_by(name="Hevy").first()
    if hevy_source:
        data_sources_used.append("Hevy")
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Query workouts
    workouts = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.workout_date >= start_date,
        Workout.workout_date <= end_date
    ).order_by(Workout.workout_date.desc()).all()
    
    if not workouts:
        return f"I couldn't find any workouts in the specified time range ({time_range}).", data_sources_used
    
    # Check for specific exercises
    common_exercises = ['bench press', 'squat', 'deadlift', 'pull up', 'shoulder press', 'bicep curl']
    for exercise_name in common_exercises:
        if exercise_name in query_text:
            # Find the exercise
            exercise = Exercise.query.filter(Exercise.name.ilike(f'%{exercise_name}%')).first()
            if not exercise:
                continue
            
            # Find workout exercises
            workout_exercises = []
            for workout in workouts:
                exercises = WorkoutExercise.query.filter_by(
                    workout_id=workout.id,
                    exercise_id=exercise.id
                ).all()
                
                for ex in exercises:
                    workout_exercises.append({
                        'workout_date': workout.workout_date,
                        'sets': ex.sets,
                        'reps': ex.reps,
                        'weight': ex.weight
                    })
            
            if not workout_exercises:
                return f"I couldn't find any {exercise.name} exercises in the specified time range ({time_range}).", data_sources_used
            
            # Sort by date, most recent first
            workout_exercises.sort(key=lambda x: x['workout_date'], reverse=True)
            
            # Calculate progress
            if len(workout_exercises) > 1 and all(ex['weight'] for ex in workout_exercises):
                latest = workout_exercises[0]
                oldest = workout_exercises[-1]
                
                weight_change = latest['weight'] - oldest['weight']
                weight_change_pct = (weight_change / oldest['weight']) * 100 if oldest['weight'] else 0
                
                response = f"For {exercise.name}, your most recent workout on {latest['workout_date'].strftime('%B %d')} was {latest['sets']} sets of {latest['reps']} reps at {latest['weight']}kg. "
                
                if abs(weight_change_pct) > 5:  # Only mention if change is significant
                    if weight_change > 0:
                        response += f"You've increased your weight by {weight_change:.1f}kg ({weight_change_pct:.1f}%) since {oldest['workout_date'].strftime('%B %d')}."
                    else:
                        response += f"Your weight has decreased by {abs(weight_change):.1f}kg ({abs(weight_change_pct):.1f}%) since {oldest['workout_date'].strftime('%B %d')}."
                
                return response, data_sources_used
            else:
                latest = workout_exercises[0]
                return f"For {exercise.name}, your most recent workout on {latest['workout_date'].strftime('%B %d')} was {latest['sets']} sets of {latest['reps']} reps at {latest['weight']}kg.", data_sources_used
    
    # Check for specific metrics
    if 'volume' in query_text:
        total_volume = 0
        for workout in workouts:
            exercises = WorkoutExercise.query.filter_by(workout_id=workout.id).all()
            for ex in exercises:
                if ex.sets and ex.reps and ex.weight:
                    total_volume += ex.sets * ex.reps * ex.weight
        
        avg_volume = total_volume / len(workouts) if workouts else 0
        return f"Your total workout volume was {total_volume:.0f}kg, averaging {avg_volume:.0f}kg per workout.", data_sources_used
    
    if 'duration' in query_text or 'time' in query_text:
        total_duration = sum(workout.duration for workout in workouts if workout.duration)
        avg_duration = total_duration / len(workouts) if workouts else 0
        
        return f"You spent a total of {total_duration//3600} hours and {(total_duration%3600)//60} minutes working out, averaging {avg_duration//60:.0f} minutes per session.", data_sources_used
    
    if 'calories' in query_text:
        total_calories = sum(workout.calories_burned for workout in workouts if workout.calories_burned)
        avg_calories = total_calories / len(workouts) if workouts else 0
        
        return f"You burned approximately {total_calories:.0f} calories in total during your workouts, averaging {avg_calories:.0f} calories per session.", data_sources_used
    
    # Default summary
    workout_names = {}
    for workout in workouts:
        name = workout.workout_name
        if name in workout_names:
            workout_names[name] += 1
        else:
            workout_names[name] = 1
    
    most_frequent = sorted(workout_names.items(), key=lambda x: x[1], reverse=True)
    
    total_duration = sum(workout.duration for workout in workouts if workout.duration)
    total_calories = sum(workout.calories_burned for workout in workouts if workout.calories_burned)
    
    response = f"During this period ({time_range}), you completed {len(workouts)} workouts. "
    
    if most_frequent:
        response += "Your most frequent workout types were: "
        for name, count in most_frequent[:3]:
            response += f"{name} ({count} times), "
        response = response.rstrip(', ') + ". "
    
    if total_duration:
        response += f"You spent a total of {total_duration//3600} hours and {(total_duration%3600)//60} minutes exercising. "
    
    if total_calories:
        response += f"You burned approximately {total_calories:.0f} calories during these workouts."
    
    return response, data_sources_used

def process_summary_query(user_id, query_text):
    """Process a summary query about overall health"""
    data_sources_used = []
    
    # Determine time range
    time_range = extract_time_range(query_text)
    start_date, end_date = get_date_range(time_range)
    
    # Get activity summary
    activity_response, activity_sources = process_activity_query(user_id, f"activity summary {time_range}")
    if "I couldn't find" not in activity_response:
        data_sources_used.extend(activity_sources)
    
    # Get food summary
    food_response, food_sources = process_food_query(user_id, f"food summary {time_range}")
    if "I couldn't find" not in food_response:
        data_sources_used.extend(food_sources)
    
    # Get sleep summary
    sleep_response, sleep_sources = process_sleep_query(user_id, f"sleep summary {time_range}")
    if "I couldn't find" not in sleep_response:
        data_sources_used.extend(sleep_sources)
    
    # Get workout summary
    workout_response, workout_sources = process_workout_query(user_id, f"workout summary {time_range}")
    if "I couldn't find" not in workout_response:
        data_sources_used.extend(workout_sources)
    
    # Compile response
    response = f"Here's your health summary for {time_range}:\n\n"
    
    if "I couldn't find" not in activity_response:
        response += f"Activity: {activity_response}\n\n"
    
    if "I couldn't find" not in sleep_response:
        response += f"Sleep: {sleep_response}\n\n"
    
    if "I couldn't find" not in food_response:
        response += f"Nutrition: {food_response}\n\n"
    
    if "I couldn't find" not in workout_response:
        response += f"Workouts: {workout_response}\n\n"
    
    # Generate insights
    insights = create_insights_for_user(user_id, start_date, end_date)
    if insights:
        response += "Insights:\n"
        for insight in insights[:3]:  # Show top 3 insights
            response += f"- {insight.insight_text}\n"
    
    return response, data_sources_used

def process_comparison_query(user_id, query_text):
    """Process a comparison query between different time periods or metrics"""
    data_sources_used = []
    
    # Check for time period comparison
    time_periods = ['today', 'yesterday', 'this week', 'last week', 'this month', 'last month']
    period_pairs = []
    
    for i, period1 in enumerate(time_periods):
        for period2 in time_periods[i+1:]:
            if period1 in query_text and period2 in query_text:
                period_pairs.append((period1, period2))
    
    if period_pairs:
        period1, period2 = period_pairs[0]  # Take the first pair found
        
        # Determine what to compare
        if 'activity' in query_text or 'steps' in query_text:
            response1, sources1 = process_activity_query(user_id, f"activity {period1}")
            response2, sources2 = process_activity_query(user_id, f"activity {period2}")
            data_sources_used.extend(sources1 + sources2)
            
            return f"Comparing activities:\n\n{period1.capitalize()}: {response1}\n\n{period2.capitalize()}: {response2}", data_sources_used
        
        elif 'food' in query_text or 'calories' in query_text or 'nutrition' in query_text:
            response1, sources1 = process_food_query(user_id, f"food {period1}")
            response2, sources2 = process_food_query(user_id, f"food {period2}")
            data_sources_used.extend(sources1 + sources2)
            
            return f"Comparing nutrition:\n\n{period1.capitalize()}: {response1}\n\n{period2.capitalize()}: {response2}", data_sources_used
        
        elif 'sleep' in query_text:
            response1, sources1 = process_sleep_query(user_id, f"sleep {period1}")
            response2, sources2 = process_sleep_query(user_id, f"sleep {period2}")
            data_sources_used.extend(sources1 + sources2)
            
            return f"Comparing sleep:\n\n{period1.capitalize()}: {response1}\n\n{period2.capitalize()}: {response2}", data_sources_used
        
        elif 'workout' in query_text or 'exercise' in query_text:
            response1, sources1 = process_workout_query(user_id, f"workout {period1}")
            response2, sources2 = process_workout_query(user_id, f"workout {period2}")
            data_sources_used.extend(sources1 + sources2)
            
            return f"Comparing workouts:\n\n{period1.capitalize()}: {response1}\n\n{period2.capitalize()}: {response2}", data_sources_used
        
        else:
            # Default to overall summary comparison
            response1, sources1 = process_summary_query(user_id, f"summary {period1}")
            response2, sources2 = process_summary_query(user_id, f"summary {period2}")
            data_sources_used.extend(sources1 + sources2)
            
            return f"Comparing health summaries:\n\n{period1.capitalize()}:\n{response1}\n\n{period2.capitalize()}:\n{response2}", data_sources_used
    
    # Check for metric comparison
    metrics = ['steps', 'calories', 'sleep', 'heart rate', 'weight']
    metric_pairs = []
    
    for i, metric1 in enumerate(metrics):
        for metric2 in metrics[i+1:]:
            if metric1 in query_text and metric2 in query_text:
                metric_pairs.append((metric1, metric2))
    
    if metric_pairs:
        metric1, metric2 = metric_pairs[0]  # Take the first pair found
        time_range = extract_time_range(query_text) or "this week"
        
        # Get data for each metric
        if metric1 == 'steps':
            response1, sources1 = process_activity_query(user_id, f"steps {time_range}")
            data_sources_used.extend(sources1)
        elif metric1 == 'calories':
            response1, sources1 = process_food_query(user_id, f"calories {time_range}")
            data_sources_used.extend(sources1)
        elif metric1 == 'sleep':
            response1, sources1 = process_sleep_query(user_id, f"sleep duration {time_range}")
            data_sources_used.extend(sources1)
        elif metric1 == 'heart rate':
            response1, sources1 = process_activity_query(user_id, f"heart rate {time_range}")
            data_sources_used.extend(sources1)
        elif metric1 == 'weight':
            response1, sources1 = process_workout_query(user_id, f"weight {time_range}")
            data_sources_used.extend(sources1)
        
        if metric2 == 'steps':
            response2, sources2 = process_activity_query(user_id, f"steps {time_range}")
            data_sources_used.extend(sources2)
        elif metric2 == 'calories':
            response2, sources2 = process_food_query(user_id, f"calories {time_range}")
            data_sources_used.extend(sources2)
        elif metric2 == 'sleep':
            response2, sources2 = process_sleep_query(user_id, f"sleep duration {time_range}")
            data_sources_used.extend(sources2)
        elif metric2 == 'heart rate':
            response2, sources2 = process_activity_query(user_id, f"heart rate {time_range}")
            data_sources_used.extend(sources2)
        elif metric2 == 'weight':
            response2, sources2 = process_workout_query(user_id, f"weight {time_range}")
            data_sources_used.extend(sources2)
        
        return f"Comparing {metric1} and {metric2} for {time_range}:\n\n{metric1.capitalize()}: {response1}\n\n{metric2.capitalize()}: {response2}", data_sources_used
    
    # If no specific comparison found, provide a general response
    return "I can compare different time periods (like 'this week vs last week') or different metrics (like 'steps vs calories'). Please specify what you'd like to compare.", data_sources_used

def extract_time_range(query_text):
    """Extract time range from query text"""
    time_ranges = {
        'today': 'today',
        'yesterday': 'yesterday',
        'this week': 'this week',
        'last week': 'last week',
        'this month': 'this month',
        'last month': 'last month',
        'this year': 'this year',
        'last year': 'last year',
        'past week': 'past week',
        'past month': 'past month',
        'past year': 'past year',
        'last 7 days': 'past week',
        'last 30 days': 'past month',
        'last 365 days': 'past year'
    }
    
    for range_text, range_value in time_ranges.items():
        if range_text in query_text:
            return range_value
    
    # Default to "this week" if no time range specified
    return "this week"

def get_date_range(time_range):
    """Convert time range to start and end dates"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if time_range == 'today':
        return today, today + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'this week':
        # Start of week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week, today + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'last week':
        # Start of last week (Monday)
        start_of_last_week = today - timedelta(days=today.weekday() + 7)
        end_of_last_week = start_of_last_week + timedelta(days=7) - timedelta(microseconds=1)
        return start_of_last_week, end_of_last_week
    
    elif time_range == 'this month':
        # Start of month
        start_of_month = today.replace(day=1)
        return start_of_month, today + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'last month':
        # Start of last month
        if today.month == 1:
            start_of_last_month = today.replace(year=today.year-1, month=12, day=1)
        else:
            start_of_last_month = today.replace(month=today.month-1, day=1)
        
        # End of last month
        end_of_last_month = today.replace(day=1) - timedelta(microseconds=1)
        return start_of_last_month, end_of_last_month
    
    elif time_range == 'this year':
        # Start of year
        start_of_year = today.replace(month=1, day=1)
        return start_of_year, today + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'last year':
        # Start of last year
        start_of_last_year = today.replace(year=today.year-1, month=1, day=1)
        # End of last year
        end_of_last_year = today.replace(year=today.year-1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        return start_of_last_year, end_of_last_year
    
    elif time_range == 'past week':
        return today - timedelta(days=7), today + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'past month':
        return today - timedelta(days=30), today + timedelta(days=1) - timedelta(microseconds=1)
    
    elif time_range == 'past year':
        return today - timedelta(days=365), today + timedelta(days=1) - timedelta(microseconds=1)
    
    else:
        # Default to this week
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week, today + timedelta(days=1) - timedelta(microseconds=1)

def create_insights_for_user(user_id, start_date=None, end_date=None):
    """Generate insights for a user based on their health data"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if not end_date:
        end_date = datetime.utcnow()
    
    # Clear existing insights
    Insight.query.filter_by(user_id=user_id).delete()
    
    insights = []
    
    # Activity insights
    activities = Activity.query.filter(
        Activity.user_id == user_id,
        Activity.start_time >= start_date,
        Activity.start_time <= end_date
    ).all()
    
    if activities:
        # Check for activity trends
        activities_by_day = {}
        for activity in activities:
            day = activity.start_time.date()
            if day in activities_by_day:
                activities_by_day[day].append(activity)
            else:
                activities_by_day[day] = [activity]
        
        # Check for days with most activities
        if len(activities_by_day) > 0:
            most_active_day = max(activities_by_day.items(), key=lambda x: len(x[1]))
            insight = Insight(
                user_id=user_id,
                insight_type='trend',
                insight_text=f"Your most active day was {most_active_day[0].strftime('%A, %B %d')} with {len(most_active_day[1])} activities.",
                data_sources=["Strava"],
                relevance_score=0.8,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(insight)
            insights.append(insight)
        
        # Check for longest activity
        longest_activity = max(activities, key=lambda x: x.duration if x.duration else 0)
        if longest_activity.duration:
            insight = Insight(
                user_id=user_id,
                insight_type='highlight',
                insight_text=f"Your longest activity was a {longest_activity.activity_type} on {longest_activity.start_time.strftime('%B %d')} lasting {longest_activity.duration//3600} hours and {(longest_activity.duration%3600)//60} minutes.",
                data_sources=["Strava"],
                relevance_score=0.7,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(insight)
            insights.append(insight)
    
    # Sleep insights
    sleep_records = SleepRecord.query.filter(
        SleepRecord.user_id == user_id,
        SleepRecord.start_time >= start_date,
        SleepRecord.start_time <= end_date
    ).all()
    
    if sleep_records:
        # Check for sleep score trends
        records_with_score = [r for r in sleep_records if r.sleep_score]
        if records_with_score:
            best_sleep = max(records_with_score, key=lambda x: x.sleep_score)
            worst_sleep = min(records_with_score, key=lambda x: x.sleep_score)
            
            insight = Insight(
                user_id=user_id,
                insight_type='trend',
                insight_text=f"Your best sleep was on {best_sleep.start_time.strftime('%A, %B %d')} with a score of {best_sleep.sleep_score}. Your worst sleep was on {worst_sleep.start_time.strftime('%A, %B %d')} with a score of {worst_sleep.sleep_score}.",
                data_sources=["Apple Health"],
                relevance_score=0.9,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(insight)
            insights.append(insight)
        
        # Check for sleep duration trends
        avg_duration = sum(r.duration for r in sleep_records if r.duration) / len(sleep_records) if sleep_records else 0
        if avg_duration:
            if avg_duration < 6 * 3600:  # Less than 6 hours
                insight = Insight(
                    user_id=user_id,
                    insight_type='recommendation',
                    insight_text=f"Your average sleep duration of {avg_duration/3600:.1f} hours is below the recommended 7-9 hours. Consider adjusting your sleep schedule to improve overall health.",
                    data_sources=["Apple Health"],
                    relevance_score=0.95,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(insight)
                insights.append(insight)
            elif avg_duration > 9 * 3600:  # More than 9 hours
                insight = Insight(
                    user_id=user_id,
                    insight_type='observation',
                    insight_text=f"Your average sleep duration of {avg_duration/3600:.1f} hours is above the typical recommendation. While individual needs vary, consistently sleeping more than 9 hours might be worth discussing with a healthcare provider.",
                    data_sources=["Apple Health"],
                    relevance_score=0.7,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(insight)
                insights.append(insight)
    
    # Nutrition insights
    food_entries = FoodEntry.query.filter(
        FoodEntry.user_id == user_id,
        FoodEntry.consumed_at >= start_date,
        FoodEntry.consumed_at <= end_date
    ).all()
    
    if food_entries:
        # Check for calorie trends
        daily_calories = {}
        for entry in food_entries:
            day = entry.consumed_at.date()
            if day in daily_calories:
                daily_calories[day] += entry.total_calories if entry.total_calories else 0
            else:
                daily_calories[day] = entry.total_calories if entry.total_calories else 0
        
        if daily_calories:
            avg_calories = sum(daily_calories.values()) / len(daily_calories)
            if avg_calories > 2500:
                insight = Insight(
                    user_id=user_id,
                    insight_type='observation',
                    insight_text=f"Your average daily calorie intake of {avg_calories:.0f} calories is relatively high. Consider reviewing your nutrition if weight management is a goal.",
                    data_sources=["HealthifyMe"],
                    relevance_score=0.8,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(insight)
                insights.append(insight)
            elif avg_calories < 1500:
                insight = Insight(
                    user_id=user_id,
                    insight_type='observation',
                    insight_text=f"Your average daily calorie intake of {avg_calories:.0f} calories is relatively low. Ensure you're getting adequate nutrition for your activity level.",
                    data_sources=["HealthifyMe"],
                    relevance_score=0.8,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(insight)
                insights.append(insight)
        
        # Check for macronutrient balance
        total_protein = sum(entry.total_protein for entry in food_entries if entry.total_protein)
        total_carbs = sum(entry.total_carbs for entry in food_entries if entry.total_carbs)
        total_fat = sum(entry.total_fat for entry in food_entries if entry.total_fat)
        
        if total_protein and total_carbs and total_fat:
            total_macros = total_protein + total_carbs + total_fat
            protein_pct = (total_protein / total_macros) * 100
            carbs_pct = (total_carbs / total_macros) * 100
            fat_pct = (total_fat / total_macros) * 100
            
            if protein_pct < 15:
                insight = Insight(
                    user_id=user_id,
                    insight_type='recommendation',
                    insight_text=f"Your protein intake is relatively low at {protein_pct:.0f}% of your macronutrients. Consider incorporating more protein-rich foods for muscle maintenance and recovery.",
                    data_sources=["HealthifyMe"],
                    relevance_score=0.85,
                    start_date=start_date,
                    end_date=end_date
                )
                db.session.add(insight)
                insights.append(insight)
    
    # Workout insights
    workouts = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.workout_date >= start_date,
        Workout.workout_date <= end_date
    ).all()
    
    if workouts:
        # Check for workout frequency
        days_with_workouts = len(set(workout.workout_date.date() for workout in workouts))
        total_days = (end_date - start_date).days + 1
        
        if days_with_workouts < total_days * 0.2:  # Less than 20% of days
            insight = Insight(
                user_id=user_id,
                insight_type='recommendation',
                insight_text=f"You worked out on {days_with_workouts} days out of {total_days} ({(days_with_workouts/total_days)*100:.0f}%). Consider increasing your workout frequency for better fitness results.",
                data_sources=["Hevy"],
                relevance_score=0.9,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(insight)
            insights.append(insight)
        elif days_with_workouts > total_days * 0.7:  # More than 70% of days
            insight = Insight(
                user_id=user_id,
                insight_type='observation',
                insight_text=f"You worked out on {days_with_workouts} days out of {total_days} ({(days_with_workouts/total_days)*100:.0f}%). That's an impressive consistency! Remember to include adequate rest days for recovery.",
                data_sources=["Hevy"],
                relevance_score=0.8,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(insight)
            insights.append(insight)
    
    # Cross-domain insights
    if activities and sleep_records:
        # Check for correlation between activity and sleep
        activity_days = set(activity.start_time.date() for activity in activities)
        sleep_days = set(record.start_time.date() for record in sleep_records)
        
        days_with_both = activity_days.intersection(sleep_days)
        if days_with_both:
            # Get sleep records for days with activity
            sleep_after_activity = []
            for day in days_with_both:
                day_activities = [a for a in activities if a.start_time.date() == day]
                next_day = day + timedelta(days=1)
                next_day_sleep = [s for s in sleep_records if s.start_time.date() == next_day]
                
                if day_activities and next_day_sleep:
                    sleep_after_activity.append((day_activities, next_day_sleep[0]))
            
            if sleep_after_activity:
                # Check if sleep quality is better after activity days
                sleep_scores_after_activity = [sleep.sleep_score for _, sleep in sleep_after_activity if sleep.sleep_score]
                all_sleep_scores = [sleep.sleep_score for sleep in sleep_records if sleep.sleep_score]
                
                if sleep_scores_after_activity and all_sleep_scores:
                    avg_after_activity = sum(sleep_scores_after_activity) / len(sleep_scores_after_activity)
                    avg_all = sum(all_sleep_scores) / len(all_sleep_scores)
                    
                    if avg_after_activity > avg_all * 1.1:  # 10% better
                        insight = Insight(
                            user_id=user_id,
                            insight_type='correlation',
                            insight_text=f"Your sleep quality tends to be better after days with physical activity. Your average sleep score after active days is {avg_after_activity:.0f} compared to your overall average of {avg_all:.0f}.",
                            data_sources=["Strava", "Apple Health"],
                            relevance_score=0.95,
                            start_date=start_date,
                            end_date=end_date
                        )
                        db.session.add(insight)
                        insights.append(insight)
    
    db.session.commit()
    return insights
