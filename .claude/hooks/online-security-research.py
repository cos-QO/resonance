#!/usr/bin/env python3
"""
online security research Hook
Enhanced Claude Code hook with standardized structure

Hook Type: PostToolUse
Purpose: ...
Triggers: Specific tool operations (see should_process method)
Dependencies: Standard Python libraries
Version: 1.0.0
"""


import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

class OnlineSecurityResearch:
    def __init__(self):
        self.project_root = self._find_project_root()
        self.memory_dir = os.path.join(self.project_root, '.claude', 'memory', 'security')
        self.cache_file = os.path.join(self.memory_dir, 'security-cache.json')
        self._ensure_directories()
    
    def _find_project_root(self):
        current = os.getcwd()
        while current != '/':
            if os.path.exists(os.path.join(current, '.claude')):
                return current
            current = os.path.dirname(current)
        return os.getcwd()
    
    def _ensure_directories(self):
        os.makedirs(self.memory_dir, exist_ok=True)
    
    def detect_security_context(self, tool_name, tool_input):
        """Detect when Security agent needs online research"""
        if tool_name != "Task":
            return False
        
        agent_type = tool_input.get("subagent_type", "")
        prompt = tool_input.get("prompt", "").lower()
        
        # Security agent is being invoked
        if agent_type == "security":
            return True
        
        # Security-related keywords in prompt
        security_keywords = [
            'vulnerability', 'cve', 'security audit', 'penetration test',
            'threat model', 'security review', 'exploit', 'backdoor',
            'injection', 'xss', 'csrf', 'authentication', 'authorization'
        ]
        
        return any(keyword in prompt for keyword in security_keywords)
    
    def get_cached_research(self, query_hash):
        """Get cached security research if available and fresh"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            if query_hash in cache:
                cached_item = cache[query_hash]
                cached_time = datetime.fromisoformat(cached_item['timestamp'])
                
                # Cache valid for 24 hours
                if datetime.now() - cached_time < timedelta(hours=24):
                    return cached_item['data']
        except:
            pass
        
        return None
    
    def cache_research(self, query_hash, data):
        """Cache security research results"""
        cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                cache = {}
        
        cache[query_hash] = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Keep only last 50 entries to prevent cache bloat
        if len(cache) > 50:
            sorted_items = sorted(cache.items(), 
                                key=lambda x: x[1]['timestamp'], 
                                reverse=True)
            cache = dict(sorted_items[:50])
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def generate_security_research_guidance(self, tool_input):
        """Generate security research guidance for the Security agent"""
        prompt = tool_input.get("prompt", "")
        
        # Extract potential technologies from prompt
        technologies = self.extract_technologies(prompt)
        
        research_guidance = []
        
        if technologies:
            research_guidance.append("🔍 **LIVE SECURITY RESEARCH REQUIRED**")
            research_guidance.append("")
            research_guidance.append("**Detected Technologies:**")
            for tech in technologies:
                research_guidance.append(f"- {tech}")
            research_guidance.append("")
            
            research_guidance.append("**Research Tasks:**")
            research_guidance.append("1. Search for recent CVE advisories for detected technologies")
            research_guidance.append("2. Look up current security best practices and patterns")
            research_guidance.append("3. Check for any security updates or patches available")
            research_guidance.append("4. Cache findings in .claude/memory/security/")
            research_guidance.append("")
            
            # Generate specific search queries
            research_guidance.append("**Suggested Search Queries:**")
            for tech in technologies:
                research_guidance.append(f"- \"{tech} security vulnerabilities 2025\"")
                research_guidance.append(f"- \"{tech} CVE recent advisories\"")
                research_guidance.append(f"- \"{tech} security best practices latest\"")
            research_guidance.append("")
        
        # Add general research guidance
        research_guidance.extend([
            "**General Security Research Protocol:**",
            "- Use WebSearch for recent security advisories and CVE databases",
            "- Check OWASP recommendations for relevant attack vectors", 
            "- Look up framework-specific security guides when applicable",
            "- Cache all findings with timestamps in security memory",
            "- Prioritize vulnerabilities by CVSS score and exploitability",
            "",
            "**Cache Location:** `.claude/memory/security/`",
            "**Cache Duration:** 24 hours for live advisories",
            ""
        ])
        
        return "\n".join(research_guidance)
    
    def extract_technologies(self, prompt):
        """Extract technology names from prompt text"""
        tech_patterns = {
            'React': r'\breact\b',
            'Node.js': r'\bnode\.?js\b',
            'Express': r'\bexpress\b',
            'Angular': r'\bangular\b',
            'Vue.js': r'\bvue\.?js\b',
            'PostgreSQL': r'\bpostgresql\b|\bpostgres\b',
            'MongoDB': r'\bmongodb\b|\bmongo\b',
            'MySQL': r'\bmysql\b',
            'Django': r'\bdjango\b',
            'Flask': r'\bflask\b',
            'Laravel': r'\blaravel\b',
            'Spring': r'\bspring\b',
            'JWT': r'\bjwt\b',
            'OAuth': r'\boauth\b',
            'Redis': r'\bredis\b',
            'Docker': r'\bdocker\b',
            'Kubernetes': r'\bkubernetes\b|\bk8s\b',
            'AWS': r'\baws\b',
            'Azure': r'\bazure\b',
            'GCP': r'\bgcp\b|\bgoogle cloud\b'
        }
        
        found_technologies = []
        prompt_lower = prompt.lower()
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                found_technologies.append(tech)
        
        return found_technologies
    
    def process_security_hook(self, tool_name, tool_input):
        """Main hook processing for security research enhancement"""
        if not self.detect_security_context(tool_name, tool_input):
            return None
        
        try:
            research_guidance = self.generate_security_research_guidance(tool_input)
            
            # Create advisory file for Security agent
            advisory_file = os.path.join(self.memory_dir, 'live-research-advisory.md')
            with open(advisory_file, 'w') as f:
                f.write("# Live Security Research Advisory\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(research_guidance)
            
            return {
                'status': 'enhanced',
                'message': f'🔍 Security research guidance generated',
                'advisory_location': advisory_file,
                'cache_location': self.memory_dir
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Security research enhancement failed: {str(e)}'
            }

def main():
    if len(sys.argv) < 4:
        return
    
    hook_type = sys.argv[1]  # 'PreToolUse' or 'PostToolUse'
    tool_name = sys.argv[2]
    tool_input = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    
    if hook_type == 'PreToolUse':
        researcher = OnlineSecurityResearch()
        result = researcher.process_security_hook(tool_name, tool_input)
        
        if result:
            print(f"[SECURITY RESEARCH] {result['message']}")
            if result.get('advisory_location'):
                print(f"[ADVISORY] {result['advisory_location']}")

if __name__ == "__main__":
    main()