import json
from html import unescape
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field


class GroundedProblem(BaseModel):
    id: str
    source: str
    title: str
    difficulty: str
    description: str
    constraints: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)
    time_target: str = "O(n)"
    space_target: str = "O(n)"


_FALLBACK = {
    "two-sum": GroundedProblem(
        id="1",
        source="leetcode",
        title="Two Sum",
        difficulty="Easy",
        description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice.",
        constraints=["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9", "Only one valid answer exists."],
        examples=[{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."}],
        time_target="O(n)",
        space_target="O(n)",
    ),
    "valid-palindrome": GroundedProblem(
        id="125",
        source="leetcode",
        title="Valid Palindrome",
        difficulty="Easy",
        description="A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Given a string s, return true if it is a palindrome, or false otherwise.",
        constraints=["1 <= s.length <= 2 * 10^5", "s consists only of printable ASCII characters."],
        examples=[{"input": 's = "A man, a plan, a canal: Panama"', "output": "true", "explanation": '"amanaplanacanalpanama" is a palindrome.'}],
        time_target="O(n)",
        space_target="O(1)",
    ),
    "reverse-linked-list": GroundedProblem(
        id="206",
        source="leetcode",
        title="Reverse Linked List",
        difficulty="Easy",
        description="Given the head of a singly linked list, reverse the list, and return the reversed list.",
        constraints=["The number of nodes in the list is the range [0, 5000].", "-5000 <= Node.val <= 5000"],
        examples=[{"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]"}],
        time_target="O(n)",
        space_target="O(1)",
    ),
    "merge-intervals": GroundedProblem(
        id="56",
        source="leetcode",
        title="Merge Intervals",
        difficulty="Medium",
        description="Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.",
        constraints=["1 <= intervals.length <= 10^4", "intervals[i].length == 2", "0 <= starti <= endi <= 10^4"],
        examples=[{"input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]", "explanation": "Intervals [1,3] and [2,6] overlap, merging them into [1,6]."}],
        time_target="O(n log n)",
        space_target="O(n)",
    ),
    "best-time-to-buy-and-sell-stock": GroundedProblem(
        id="121",
        source="leetcode",
        title="Best Time to Buy and Sell Stock",
        difficulty="Easy",
        description="You are given an array prices where prices[i] is the price of a given stock on the ith day. You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock. Return the maximum profit you can achieve from this transaction.",
        constraints=["1 <= prices.length <= 10^5", "0 <= prices[i] <= 10^4"],
        examples=[{"input": "prices = [7,1,5,3,6,4]", "output": "5", "explanation": "Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5."}],
        time_target="O(n)",
        space_target="O(1)",
    ),
}


def _strip_html(value: str) -> str:
    import re
    return unescape(re.sub(r"<[^>]+>", " ", value)).replace("\xa0", " ").strip()


def fetch_leetcode_problem(title_slug: str) -> GroundedProblem:
    slug = title_slug.strip().lower().strip("/")
    fallback = _FALLBACK.get(slug)
    url = "https://leetcode.com/graphql"
    query = {"query": "query question($titleSlug: String!) { question(titleSlug: $titleSlug) { questionId title difficulty content exampleTestcases } }", "variables": {"titleSlug": slug}}
    try:
        request = Request(url, data=json.dumps(query).encode(), headers={"Content-Type": "application/json", "User-Agent": "PrepareIt.ai/1.0"}, method="POST")
        with urlopen(request, timeout=8) as response:
            payload = json.load(response)
        question = payload.get("data", {}).get("question") or {}
        if question.get("title"):
            description = _strip_html(question.get("content", ""))
            constraints = fallback.constraints if fallback else []
            examples = fallback.examples if fallback else []
            time_target = fallback.time_target if fallback else "O(n)"
            space_target = fallback.space_target if fallback else "O(n)"
            return GroundedProblem(
                id=str(question.get("questionId", slug)),
                source="leetcode",
                title=question["title"],
                difficulty=question.get("difficulty", "Unknown"),
                description=description,
                constraints=constraints,
                examples=examples,
                time_target=time_target,
                space_target=space_target,
            )
    except (OSError, URLError, ValueError, KeyError):
        pass
    if fallback:
        return fallback
    return GroundedProblem(id=slug, source="leetcode", title=slug.replace("-", " ").title(), difficulty="Unknown", description="Problem details are unavailable. Ask the interviewer to restate the prompt.", constraints=[], examples=[])


class ProblemService:
    @staticmethod
    def fetch_codeforces_problem(contest_id: str, index: str) -> GroundedProblem:
        try:
            request = Request(f"https://codeforces.com/api/problemset.problem?contestId={contest_id}&index={index}", headers={"User-Agent": "PrepareIt.ai/1.0"})
            with urlopen(request, timeout=8) as response:
                result = json.load(response).get("result", {}).get("problems", [])
            if result:
                item = result[0]
                return GroundedProblem(id=f"{contest_id}{index}", source="codeforces", title=item["name"], difficulty=str(item.get("rating", "Unknown")), description="Use the interviewer-provided statement for this Codeforces problem.", constraints=[], examples=[])
        except (OSError, URLError, ValueError, KeyError):
            pass
        return GroundedProblem(id=f"{contest_id}{index}", source="codeforces", title=f"Codeforces {contest_id}{index}", difficulty="Unknown", description="Problem details are unavailable.", constraints=[], examples=[])

    @staticmethod
    def fetch(slug: str) -> GroundedProblem:
        if slug.startswith("cf-"):
            return GroundedProblem(id=slug, source="codeforces", title=slug[3:].replace("-", " ").title(), difficulty="Unknown", description="Codeforces problem details are unavailable.", constraints=[], examples=[])
        return fetch_leetcode_problem(slug)
