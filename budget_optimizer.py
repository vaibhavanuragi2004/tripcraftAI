from typing import Dict, List

class BudgetOptimizer:
    """
    Simplified budget allocation for travel planning
    """
    
    def __init__(self):
        # Standard budget distribution
        self.base_allocation = {
            'accommodation': 0.35,  # 35%
            'food': 0.25,          # 25%
            'transport': 0.20,     # 20%
            'activities': 0.15,    # 15%
            'shopping': 0.05       # 5%
        }
        
        # Simple destination classifications
        self.destination_types = {
            'mumbai': 'metro', 'delhi': 'metro', 'bangalore': 'metro', 'kolkata': 'metro',
            'chennai': 'metro', 'hyderabad': 'metro', 'pune': 'metro',
            'shimla': 'hill', 'manali': 'hill', 'ooty': 'hill', 'darjeeling': 'hill',
            'mussoorie': 'hill', 'nainital': 'hill',
            'goa': 'beach', 'kerala': 'beach', 'andaman': 'beach', 'pondicherry': 'beach',
            'rajasthan': 'historical', 'agra': 'historical', 'hampi': 'historical',
            'khajuraho': 'historical', 'ajanta': 'historical',
            'varanasi': 'spiritual', 'rishikesh': 'spiritual', 'haridwar': 'spiritual',
            'amritsar': 'spiritual', 'tirupati': 'spiritual'
        }
        
        # Simple multipliers by destination type
        self.type_multipliers = {
            'metro': {'accommodation': 1.2, 'food': 1.1},
            'hill': {'transport': 1.2, 'activities': 1.1},
            'beach': {'activities': 1.2, 'food': 1.1},
            'historical': {'activities': 1.3, 'shopping': 1.1},
            'spiritual': {'accommodation': 0.8, 'food': 0.8}
        }

    def get_destination_type(self, destination: str) -> str:
        """Classify destination type"""
        destination_lower = destination.lower()
        
        for dest, dest_type in self.destination_types.items():
            if dest in destination_lower:
                return dest_type
        
        return 'historical'  # Default

    def calculate_optimized_budget(self, 
                                 destination: str, 
                                 duration: int, 
                                 total_budget: float, 
                                 interests: List[str]) -> Dict[str, float]:
        """Calculate budget breakdown"""
        # Start with base allocation
        budget = {}
        for category, percentage in self.base_allocation.items():
            budget[category] = total_budget * percentage
        
        # Apply destination adjustments
        dest_type = self.get_destination_type(destination)
        if dest_type in self.type_multipliers:
            for category, multiplier in self.type_multipliers[dest_type].items():
                budget[category] *= multiplier
        
        # Apply interest adjustments
        for interest in interests:
            interest_lower = interest.lower()
            if 'cultural' in interest_lower or 'historical' in interest_lower:
                budget['activities'] *= 1.3
                budget['shopping'] *= 1.2
            elif 'food' in interest_lower or 'culinary' in interest_lower:
                budget['food'] *= 1.4
            elif 'shopping' in interest_lower:
                budget['shopping'] *= 1.5
            elif 'adventure' in interest_lower or 'sports' in interest_lower:
                budget['activities'] *= 1.4
        
        # Duration adjustments
        if duration > 5:
            budget['transport'] *= 0.8
            budget['accommodation'] *= 1.1
        elif duration <= 2:
            budget['transport'] *= 1.2
        
        # Normalize to maintain total budget
        total_allocated = sum(budget.values())
        factor = total_budget / total_allocated
        
        for category in budget:
            budget[category] = round(budget[category] * factor)
        
        return budget

    def get_budget_recommendations(self, 
                                 destination: str, 
                                 duration: int, 
                                 total_budget: float,
                                 interests: List[str]) -> Dict:
        """Get budget breakdown with recommendations"""
        budget_breakdown = self.calculate_optimized_budget(
            destination, duration, total_budget, interests
        )
        
        daily_budget = total_budget / duration if duration > 0 else total_budget
        
        # Budget tier classification
        if daily_budget < 2000:
            budget_tier = "budget"
            tips = [
                "Stay in hostels or budget hotels",
                "Eat at local restaurants and street food",
                "Use public transport",
                "Focus on free attractions"
            ]
        elif daily_budget < 4000:
            budget_tier = "mid-range"
            tips = [
                "Stay in mid-range hotels",
                "Mix of local and good restaurants",
                "Use metro and ride-sharing",
                "Include popular paid attractions"
            ]
        else:
            budget_tier = "premium"
            tips = [
                "Stay in premium hotels",
                "Dine at excellent restaurants",
                "Use private transport when convenient",
                "Include premium experiences"
            ]
        
        return {
            'budget_breakdown': budget_breakdown,
            'daily_budget': round(daily_budget),
            'budget_tier': budget_tier,
            'tips': tips,
            'destination_type': self.get_destination_type(destination)
        }
