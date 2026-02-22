export interface TemplateColors {
  bg: string;
  accent: string;
  text: string;
  muted: string;
}

export interface Template {
  id: string;
  name: string;
  category: "Business" | "Education" | "Creative" | "Minimal" | "Tech";
  description: string;
  tags: string[];
  colors: TemplateColors;
  popular?: boolean;
  new?: boolean;
}
