import { PublicIndexEntry } from "@/components/public/public-index-entry";

import { PublicIndexList } from "@/components/public/public-index-list";

import { PublicPageHero } from "@/components/public/public-page-hero";

import { PublicPageShell } from "@/components/public/public-page-shell";

import { publicMainWidthClass } from "@/components/public/public-ui";

import { listPublishedShowcases } from "@/lib/showcases/items";

import { createPublicMetadata } from "@/lib/seo/metadata";

import { cn } from "@/lib/utils";



export const metadata = createPublicMetadata({

  title: "AI Lab Showcases | AI Lab Portal",

  description: "Client-ready AI Lab showcases with human-reviewed delivery stories.",

  path: "/showcases",

});



// ISR: showcase content is relatively stable; revalidate every 5 minutes.
export const revalidate = 300;



export default async function ShowcasesIndexPage() {

  const showcases = await listPublishedShowcases();



  return (

    <PublicPageShell currentPath="/showcases">

      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>

        <PublicPageHero

          description="Published showcases explain how AI Lab packages combine automation with human review. Draft work stays private."

          eyebrow="AI Lab Showcases"

          title="Practical AI delivery stories."

        />



        <PublicIndexList

          emptyDescription="Client-ready showcases will appear here after publishing."

          emptyTitle="No published showcases yet"

          isEmpty={showcases.length === 0}

        >

          {showcases.map((showcase) => (

            <PublicIndexEntry

              key={showcase.slug}

              excerpt={showcase.heroSummary}

                href={`/showcases/${showcase.slug}`}
                imageUrl={showcase.imageUrl ?? undefined}

              meta={

                <>

                  {[showcase.industry, showcase.useCase].filter(Boolean).join(" · ") || "AI Lab showcase"}

                  {" · "}

                  {new Date(showcase.publishedAt).toLocaleDateString("en-US")}

                </>

              }

                title={showcase.title}

            />

          ))}

        </PublicIndexList>

      </section>

    </PublicPageShell>

  );

}

