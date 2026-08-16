export interface VoiceLanguage {
  code: string;
  name: string;
  native_name: string;
  /** BCP-47 tag for the browser Web Speech API fallback. */
  speech_code: string;
}

export interface VoiceCapabilities {
  server_stt: boolean;
  server_tts: boolean;
  translation: boolean;
  auto_detect: boolean;
  languages: VoiceLanguage[];
  default_language: string;
}

export interface TranscriptionResult {
  transcript: string;
  detected_language: string | null;
  translated_to_english: boolean;
  request_id: string | null;
}

export interface Me {
  id: number;
  username: string | null;
  email: string;
  level: number | null;
  level_label: string | null;
  ability: number | null;
  placement_completed: boolean;
  preferred_language: string;
  has_curriculum: boolean;
}

export interface PlacementQuestion {
  id: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  skill_tag: string;
  difficulty: number;
}

export interface PlacementProgress {
  answered: number;
  min_questions: number;
  max_questions: number;
  fraction: number;
}

export interface PlacementStep {
  session_id: number;
  status: 'in_progress' | 'completed';
  question: PlacementQuestion | null;
  progress: PlacementProgress;
  level: number | null;
  level_label: string | null;
}

export interface DetailedResult {
  question_id: number;
  question_text: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  skill_tag: string;
  explanation: string | null;
}

export interface SkillBreakdown {
  skill: string;
  level: number;
  questions_answered: number;
  correct: number;
}

export interface FocusArea {
  skill: string;
  why_it_matters: string;
  what_to_do: string;
}

export interface StudyWeek {
  week: number;
  focus: string;
  activities: string[];
}

export interface LiteracyReport {
  placement_session_id: number;
  level: number;
  level_label: string;
  ability: number;
  standard_error: number;
  questions_answered: number;
  questions_correct: number;
  skill_levels: SkillBreakdown[];
  summary: string;
  strengths: string[];
  focus_areas: FocusArea[];
  curriculum_rationale: string;
  study_plan: StudyWeek[];
  encouragement: string;
  generated_by: 'anthropic' | 'rule_based';
  review: DetailedResult[];
  curriculum_plan_id: number | null;
}

export interface ModuleSummary {
  id: number;
  order_index: number;
  skill_tag: string;
  title: string;
  objective: string;
  start_level: number;
  target_level: number;
  status: 'locked' | 'available' | 'in_progress' | 'passed';
  best_score: number | null;
  lessons_total: number;
  lessons_completed: number;
}

export interface LessonSummary {
  id: number;
  order_index: number;
  title: string;
  objective: string;
  estimated_minutes: number;
  completed: boolean;
}

export interface PracticeAttempt {
  id: number;
  score: number;
  total: number;
  percentage: number;
  passed: boolean;
  level_before: number | null;
  level_after: number | null;
  taken_at: string;
}

export interface ModuleDetail extends ModuleSummary {
  lessons: LessonSummary[];
  attempts: PracticeAttempt[];
}

export interface LessonDetail extends LessonSummary {
  module_id: number;
  module_title: string;
  skill_tag: string;
  body_markdown: string;
  read_aloud_text: string | null;
  next_lesson_id: number | null;
  prev_lesson_id: number | null;
}

export interface Curriculum {
  plan_id: number;
  title: string;
  level: number;
  level_label: string;
  rationale: string;
  modules: ModuleSummary[];
  overall_progress: number;
}

export interface PracticeTest {
  practice_session_id: number;
  module_id: number;
  module_title: string;
  skill_tag: string;
  pass_mark: number;
  questions: PlacementQuestion[];
}

export interface PracticeResult {
  score: number;
  total: number;
  percentage: number;
  passed: boolean;
  pass_mark: number;
  module_status: string;
  level_before: number | null;
  level_after: number | null;
  level_changed: boolean;
  next_module_id: number | null;
  feedback: string;
  review: DetailedResult[];
}
