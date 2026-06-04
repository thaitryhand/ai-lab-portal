import type { Metadata } from "next";

import { AiNewsSubmitForm } from "./submit-form";

export const metadata: Metadata = {
  title: "Submit AI news | AI Lab Portal",
  description: "Suggest an AI-related article or announcement for review.",
};

export default function AiNewsSubmitPage() {
  return <AiNewsSubmitForm />;
}
